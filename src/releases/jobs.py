import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.db import connection
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore, register_events
from resources import calculate_characteristics

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from entity_trees.services import resolve_release_configuration
from organizations.models import Repository
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic

logger = logging.getLogger(__name__)

# Chave fixa do advisory lock de sessao do Postgres usado para eleger um
# unico worker como dono do scheduler. Qualquer int de 64 bits estavel
# serve, contanto que seja o mesmo em todos os workers do mesmo banco.
SCHEDULER_ADVISORY_LOCK_KEY = 728_945_113


def get_releases_and_create_results():
    today = timezone.now()
    today_min = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_max = today.replace(hour=23, minute=59, second=59, microsecond=59)

    releases = list(
        Release.objects.filter(end_at__lte=today_max, end_at__gte=today_min)
        .select_related("product")
        .prefetch_related("repositories")
    )

    if not releases:
        return

    configurations = {release.id: resolve_release_configuration(release.product, release) for release in releases}
    latest_subcharacteristic_values = _get_latest_subcharacteristic_values(configurations.values())
    characteristics = SupportedCharacteristic.objects.in_bulk(
        {key for configuration in configurations.values() for key in configuration.get_characteristics_keys()},
        field_name="key",
    )

    for release in releases:
        repositories = list(release.repositories.all()) or list(
            Repository.objects.filter(product_id=release.product_id)  # type: ignore
        )
        if not repositories:
            continue

        # os parâmetros não dependem do repositório, então o Core calcula uma vez por release
        core_params = {
            "characteristics": _get_characteristics_params(configurations[release.id], latest_subcharacteristic_values)
        }
        calculate_result = calculate_characteristics(core_params)
        calculated_values = {
            characteristic["key"]: characteristic["value"] for characteristic in calculate_result["characteristics"]
        }

        for repository in repositories:
            _create_release_results(release, repository, characteristics, calculated_values)


def _get_latest_subcharacteristic_values(configurations) -> dict:
    """
    Último valor calculado de cada subcaracterística das configurações, numa consulta só.

    Mesma regra de `SupportedSubCharacteristic.get_latest_subcharacteristic_value`: o mais recente
    de qualquer repositório. Antes o job carregava todos os cálculos de subcaracterística do banco
    para cada repositório da release.
    """
    subcharacteristic_keys = {
        subcharacteristic["key"]
        for configuration in configurations
        for characteristic in configuration.data["characteristics"]
        for subcharacteristic in characteristic["subcharacteristics"]
    }
    latest = (
        CalculatedSubCharacteristic.objects.filter(subcharacteristic__key__in=subcharacteristic_keys)
        .order_by("subcharacteristic_id", "-created_at")
        .distinct("subcharacteristic_id")
        .values_list("subcharacteristic__key", "value")
    )
    return dict(latest)


def _get_characteristics_params(configuration, latest_values: dict) -> list:
    """
    Características da configuração da release, com o último valor de cada subcaracterística.

    Como no cálculo do modelo (`math_model/services.py`), a subcaracterística sem valor calculado fica
    de fora, e a característica sem nenhuma também, para não derrubar no Core o cálculo das outras.
    """
    params = []
    for characteristic in configuration.data["characteristics"]:
        subcharacteristics = [
            {"key": sub["key"], "value": latest_values[sub["key"]], "weight": sub["weight"]}
            for sub in characteristic["subcharacteristics"]
            if sub["weight"] and sub["key"] in latest_values
        ]
        if subcharacteristics:
            params.append({"key": characteristic["key"], "subcharacteristics": subcharacteristics})
    return params


def _create_release_results(release, repository, characteristics, calculated_values: dict):
    calculated_characteristics = [
        CalculatedCharacteristic(
            characteristic=characteristics[key],
            value=value,
            repository=repository,
            created_at=timezone.now(),
            release=release,
        )
        for key, value in calculated_values.items()
    ]

    try:
        CalculatedCharacteristic.objects.bulk_create(calculated_characteristics)
        logger.info(
            "Características calculadas criadas (release %s, repositório %s)",
            release.id,
            repository.id,
        )
    except Exception:
        logger.exception(
            "Erro ao criar as características calculadas (release %s, repositório %s)",
            release.id,
            repository.id,
        )


def acquire_scheduler_lock():
    """Tenta adquirir o advisory lock de sessao do scheduler.

    Com gunicorn multi-worker, releases/apps.py ready() roda uma vez por
    worker. Sem eleicao de lider, cada worker sobe seu proprio
    BackgroundScheduler e o cron dispara N vezes (uma por worker),
    duplicando CalculatedCharacteristic.

    pg_try_advisory_lock retorna True para o primeiro worker (que vira o
    dono do scheduler) e False para os demais, sem bloquear. O lock e de
    sessao: enquanto a conexao do worker dono viver, ele segura o lock.

    Retorna True se este worker deve startar o scheduler, False caso
    contrario. Em bancos que nao suportam advisory lock (ex: sqlite em
    cenarios fora de producao) cai no fallback de startar (retorna True),
    preservando o comportamento single-process historico.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_try_advisory_lock(%s)",
                [SCHEDULER_ADVISORY_LOCK_KEY],
            )
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    except Exception:
        # Banco sem suporte a advisory lock: mantem comportamento antigo.
        # Em prod com >1 worker, use GUNICORN_WORKERS=1 no container do
        # scheduler como fallback (ver start_service.sh / deploy).
        return True


def build_release_cron_trigger():
    """Cria o CronTrigger da meia-noite com timezone explicita.

    Usa settings.TIME_ZONE (America/Sao_Paulo) em vez da tz do OS do
    container, para o gatilho do cron bater com a janela do dia que
    get_releases_and_create_results computa via timezone.now() do Django.
    """
    return CronTrigger(
        hour=0,
        minute=0,
        timezone=settings.TIME_ZONE,
    )


def build_release_scheduler():
    """Cria o BackgroundScheduler com timezone explicita (settings.TIME_ZONE).

    Evita depender da tz do OS do container, mantendo o scheduler alinhado
    com o CronTrigger e com a janela de dados do job.
    """
    return BackgroundScheduler(timezone=settings.TIME_ZONE)


def check_the_need_to_calculate_releases():
    if not acquire_scheduler_lock():
        logger.info("Scheduler ja iniciado por outro worker, ignorando...")
        return

    scheduler = build_release_scheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        get_releases_and_create_results,
        trigger=build_release_cron_trigger(),
        name="get_releases_and_create_results",
        jobstore="default",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=10,
        coalesce=True,
        id="get_releases_and_create_results",
    )
    register_events(scheduler)
    scheduler.start()
    logger.info("Scheduler started...")
