"""
Dados dos dashboards por release (US07.01): Visão Geral de Qualidade, Evolução
Temporal e gráfico da tela do repositório, para o Front desenhar sem o Grafana.

O valor de uma entidade numa release é o último calculado dentro da janela da
release (ver `releases.service.get_latest_values_in_release_window`).
"""

from statistics import mean, pstdev

from metrics.models import CollectedMetric
from releases.entity_analysis import (
    CHARACTERISTIC,
    MEASURE,
    METRIC,
    SUBCHARACTERISTIC,
    get_configured_entities,
    get_entity_names,
    get_entity_values,
    get_release_repositories,
    serialize_value,
    unique_by_key,
)
from releases.models import Release
from releases.service import filter_release_window
from tsqmi.models import TSQMI

TOTALS = {
    CHARACTERISTIC: "characteristics",
    SUBCHARACTERISTIC: "subcharacteristics",
    MEASURE: "measures",
    METRIC: "metrics",
}


def get_release_summary(release: Release, configuration) -> dict:
    """
    Totais da Visão Geral na release. Cada total conta entidades distintas, e não
    linhas do histórico: as entidades da configuração da release, os repositórios
    com análise na janela da release e os arquivos (`qualifier = FIL`) coletados nela.
    """
    entities = get_configured_entities(configuration) if configuration else None
    repositories_ids = [repository.id for repository in get_release_repositories(release)]

    analyzed_repositories = (
        filter_release_window(TSQMI.objects.filter(repository_id__in=repositories_ids), release)
        .order_by()
        .values("repository_id")
        .distinct()
        .count()
    )
    # o mesmo caminho em dois repositórios são dois arquivos
    analyzed_files = (
        filter_release_window(
            CollectedMetric.objects.filter(
                repository_id__in=repositories_ids,
                qualifier="FIL",
                path__isnull=False,
            ),
            release,
        )
        .order_by()
        .values("repository_id", "path")
        .distinct()
        .count()
    )

    return {
        "release": serialize_release(release),
        "totals": {
            **{total: len(unique_by_key(entities[level])) if entities else 0 for level, total in TOTALS.items()},
            "repositories": analyzed_repositories,
            "files": analyzed_files,
        },
    }


def get_release_characteristics(release: Release, configuration) -> dict:
    """
    Valor de cada característica da configuração em cada repositório da release
    (radar) e, por característica, o planejado (meta da release) e a média e o
    desvio padrão entre os repositórios (planejado × realizado). Traz também o
    TSQMI de cada repositório na release.
    """
    keys = get_configured_keys(configuration, CHARACTERISTIC)
    names = get_entity_names(CHARACTERISTIC, keys)
    repositories = get_release_repositories(release)
    repositories_ids = [repository.id for repository in repositories]

    values = get_entity_values(CHARACTERISTIC, release, repositories_ids, keys)
    tsqmis = _get_latest_tsqmis(release, repositories_ids)

    characteristics = []
    for key in keys:
        accomplished = [values[(id_, key)].value for id_ in repositories_ids if (id_, key) in values]
        characteristics.append(
            {
                "key": key,
                "name": names.get(key, key),
                "planned": _get_planned(release, key),
                "accomplished": mean(accomplished) if accomplished else None,
                "dispersion": pstdev(accomplished) if accomplished else None,
            }
        )

    return {
        "release": serialize_release(release),
        "characteristics": characteristics,
        "repositories": [
            {
                "id": repository.id,
                "name": repository.name,
                "tsqmi": serialize_value(tsqmis.get(repository.id)),
                "characteristics": [{"key": key, **serialize_value(values.get((repository.id, key)))} for key in keys],
            }
            for repository in repositories
        ],
    }


def get_repository_release_history(repository, level: str, keys: list) -> dict:
    """
    Um ponto por release para cada entidade do nível no repositório (Evolução
    Temporal e tela do repositório). Entram as releases do produto em que o
    repositório está em `get_release_repositories`, da mais antiga para a mais nova.
    """
    releases = [
        release
        for release in Release.objects.filter(product_id=repository.product_id)
        .select_related("product")
        .order_by("start_at", "id")
        if repository.id in {item.id for item in get_release_repositories(release)}
    ]
    names = get_entity_names(level, keys)
    # chaves que não existem no sistema ficam de fora
    keys = [key for key in keys if key in names]

    values_by_release = {release.id: get_entity_values(level, release, [repository.id], keys) for release in releases}

    return {
        "repository": {"id": repository.id, "name": repository.name},
        "level": level,
        "releases": [serialize_release(release) for release in releases],
        "entities": [
            {
                "key": key,
                "name": names[key],
                "history": [
                    {
                        "release_id": release.id,
                        **serialize_value(values_by_release[release.id].get((repository.id, key))),
                    }
                    for release in releases
                ],
            }
            for key in keys
        ],
    }


def get_configured_keys(configuration, level: str) -> list:
    """Chaves das entidades do nível na configuração, sem repetição e na ordem dela."""
    if configuration is None:
        return []
    return [item["key"] for item in unique_by_key(get_configured_entities(configuration)[level])]


def serialize_release(release: Release) -> dict:
    return {
        "id": release.id,
        "release_name": release.release_name,
        "start_at": release.start_at,
        "end_at": release.end_at,
    }


def _get_planned(release: Release, key: str):
    goal = release.goal.data.get(key)
    return goal / 100 if goal is not None else None


def _get_latest_tsqmis(release: Release, repositories_ids: list) -> dict:
    latest = (
        filter_release_window(TSQMI.objects.filter(repository_id__in=repositories_ids), release)
        .order_by("repository_id", "-created_at", "-id")
        .distinct("repository_id")
    )
    return {item.repository_id: item for item in latest}
