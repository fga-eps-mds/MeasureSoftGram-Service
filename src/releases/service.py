import logging

import numpy as np
from core.transformations import diff, norm_diff
from django.db.models import QuerySet
from django.utils import timezone

from characteristics.models import CalculatedCharacteristic
from releases.models import Release

logger = logging.getLogger(__name__)


def calculate_diff(planned, accomplished):
    """
    Calcula Rc = max(0, Rp - Rd) (função `diff` do Core) para cada característica realizada.

    Rp e Rd são associados pelo nome da característica. Uma característica realizada que não
    foi planejada não tem Rp; ela fica com `diff = None` em vez de desalinhar os vetores.
    """
    planned_values = {item["name"]: item["value"] for item in planned}

    for repo in accomplished:
        comparable = [
            characteristic for characteristic in repo["characteristics"] if characteristic["name"] in planned_values
        ]

        rp = [planned_values[characteristic["name"]] for characteristic in comparable]
        rd = [characteristic["value"] for characteristic in comparable]
        diff_by_name = dict(zip((c["name"] for c in comparable), diff(rp, rd)))

        for characteristic in repo["characteristics"]:
            characteristic["diff"] = diff_by_name.get(characteristic["name"])

    return accomplished


def get_planned_values(release: Release):
    planned_values = []

    for characteristic_name, characteristic_value in release.goal.data.items():
        characteristic = {
            "name": characteristic_name,
            "value": characteristic_value / 100,
        }

        planned_values.append(characteristic)

    return planned_values


def get_accomplished_values(release: Release, repositories_ids: list[int]):
    # Todos os cálculos da release, do mais recente para o mais antigo. A deduplicação em
    # get_process_calculated_characteristics_to_list mantém o valor mais recente de cada
    # característica por repositório. (Antes havia um [:2], que limitava a resposta às duas
    # últimas características calculadas e escondia as demais.)
    result_calculated = (
        CalculatedCharacteristic.objects.filter(release=release)
        .select_related("repository", "characteristic")
        .order_by("-created_at")
    )

    if len(result_calculated) == 0:
        result_calculated = get_calculated_characteristic_by_ids_repositories(repositories_ids)

    return get_process_calculated_characteristics_to_list(list(result_calculated))


def get_process_calculated_characteristics_to_list(
    result_calculated: list[CalculatedCharacteristic],
):
    accomplished = []
    for calculated_characteristic in result_calculated:

        repository_name = calculated_characteristic.repository.name
        characteristic_name = calculated_characteristic.characteristic.key
        characteristic_value = calculated_characteristic.value

        characteristic = {
            "name": characteristic_name,
            "value": characteristic_value,
        }

        isRepositoryInserted = False

        for repository in accomplished:
            if repository["repository_name"] == repository_name:
                isRepositoryInserted = True
                if all(
                    characteristic["name"] != characteristic_name for characteristic in repository["characteristics"]
                ):
                    repository["characteristics"].append(characteristic)

        if not isRepositoryInserted:
            accomplished.append(
                {
                    "repository_name": repository_name,
                    "characteristics": [characteristic],
                }
            )

    return accomplished


def get_norm_diff(planned_values, accomplished_values):
    planned_names = {characteristic["name"] for characteristic in planned_values}

    for repository in accomplished_values:
        # só as características planejadas entram na diferença normalizada
        planned_characteristics = [
            characteristic
            for characteristic in repository["characteristics"]
            if characteristic["name"] in planned_names
        ]
        repository["norm_diff"] = calculate_norm_diff(planned_values, planned_characteristics)

    return accomplished_values


def calculate_norm_diff(planned_values, accomplished_characteristics):
    if len(planned_values) != len(accomplished_characteristics):
        logger.warning("The number of planned and accomplished characteristics should be the same.")
        return None

    else:
        rp = []
        rd = []

        for planned_characteristic in planned_values:
            planned_characteristic_name = planned_characteristic["name"]

            rp.append(planned_characteristic["value"])
            accomplished_value = None

            for accomplished_characteristic in accomplished_characteristics:
                if accomplished_characteristic["name"] == planned_characteristic_name:
                    accomplished_value = accomplished_characteristic["value"]

            if accomplished_value is None:
                logger.warning(
                    "Planned characteristic %s was not found in the accomplished characteristics.",
                    planned_characteristic_name,
                )
                return None

            if accomplished_value < 0 or accomplished_value > 1:
                logger.warning("Accomplished characteristic value should be between 0 and 1.")
                return None

            rd.append(accomplished_value)

        # norm_diff divide pela norma do planejado: com a meta toda em 0, o resultado seria inf (ou nan), que não
        # cabe no JSON e derrubava o analysis_data da release
        if not np.any(rp):
            logger.warning("The planned values are all zero: the normalized difference is undefined.")
            return None

        return norm_diff(np.array(rp), np.array(rd))


def get_process_calculated_characteristics(
    result_calculated: list[CalculatedCharacteristic],
):
    accomplished = {}
    for calculated_characteristic in result_calculated:
        characteristic = calculated_characteristic.characteristic.key
        repository = calculated_characteristic.repository.name

        if repository not in accomplished:
            accomplished[repository] = {}
        # os cálculos chegam do mais recente para o mais antigo: mantém o mais recente
        accomplished[repository].setdefault(characteristic, calculated_characteristic.value)
    return accomplished


def get_calculated_characteristic_by_ids_repositories(
    ids_repositories: list[int],
):
    result_calculated = []
    for id_repository in ids_repositories:
        # todos os cálculos do repositório (sem o antigo [:2]); a deduplicação mantém o mais recente
        calculated_characteristic = (
            CalculatedCharacteristic.objects.filter(repository_id=id_repository, release=None)
            .select_related("repository", "characteristic")
            .order_by("-created_at")
        )
        result_calculated = result_calculated + list(calculated_characteristic)
    return result_calculated


def get_arrays_diff(goal_data: dict, characteristic_repo: dict):
    array_rp = []
    array_rd = []

    for characteristic in (
        "reliability",
        "maintainability",
        "functional_suitability",
    ):
        try:
            if goal_data[characteristic] and characteristic_repo[characteristic]:
                array_rp.append(goal_data[characteristic] / 100)
                array_rd.append(characteristic_repo[characteristic])
        except Exception:
            continue

    return array_rp, array_rd


def update_release_end_at(release_id: int, new_end_at):
    """
    Atualiza o campo `end_at` de uma Release.

    :param release_id: ID da Release a ser atualizada.
    :param new_end_at: Novo valor para o campo `end_at`.
    :return: A Release atualizada.
    """
    release = Release.objects.get(id=release_id)
    release.end_at = new_end_at
    release.save()

    return release


def filter_release_window(queryset: QuerySet, release: Release) -> QuerySet:
    """
    Restringe um queryset de valores calculados/coletados à janela da release.

    A janela vai do dia de `start_at` ao dia de `end_at`, ambos inclusive, no fuso do
    projeto. As datas da release são gravadas à meia-noite, então comparar o horário
    exato deixaria de fora tudo o que foi calculado no último dia.
    """
    return queryset.filter(
        created_at__date__gte=timezone.localtime(release.start_at).date(),
        created_at__date__lte=timezone.localtime(release.end_at).date(),
    )


def get_latest_values_in_release_window(queryset: QuerySet, release: Release, entity_field: str) -> dict:
    """
    Último valor de cada entidade em cada repositório dentro da janela da release.

    Mesma regra do gráfico de pulso do TSQMI (US06.01): vale o cálculo mais recente
    feito entre `start_at` e `end_at`. `entity_field` é o nome do FK da entidade no
    model (`characteristic`, `subcharacteristic`, `measure` ou `metric`).

    Retorna `{(repository_id, entity_key): registro}`; a ausência da chave significa
    que o repositório não tem valor na release.
    """
    entity_id = f"{entity_field}_id"
    latest = (
        filter_release_window(queryset, release)
        .select_related(entity_field)
        .order_by("repository_id", entity_id, "-created_at", "-id")
        .distinct("repository_id", entity_id)
    )
    return {(item.repository_id, getattr(item, entity_field).key): item for item in latest}
