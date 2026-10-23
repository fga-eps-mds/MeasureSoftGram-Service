"""
Dados da Visão Geral de Qualidade por release (US07.01), para o Front desenhar sem o Grafana.

O planejado × realizado e o radar usam o `analysis-data` da release, e a Evolução Temporal e a
tela do repositório usam `historical-values/*` (correções do PO de 21/10). Aqui ficam os totais
e o Indicador Total da Qualidade (TSQMI) de cada repositório na release: o último calculado
dentro da janela da release (ver `releases.service.filter_release_window`).
"""

from metrics.models import CollectedMetric
from releases.entity_analysis import (
    CHARACTERISTIC,
    MEASURE,
    METRIC,
    SUBCHARACTERISTIC,
    get_configured_entities,
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


def get_release_repositories_tsqmi(release: Release) -> dict:
    """Indicador Total da Qualidade (TSQMI) de cada repositório na release; `value: null` sem análise na janela."""
    repositories = get_release_repositories(release)
    tsqmis = get_latest_tsqmis(release, [repository.id for repository in repositories])

    return {
        "release": serialize_release(release),
        "repositories": [
            {
                "id": repository.id,
                "name": repository.name,
                "tsqmi": serialize_value(tsqmis.get(repository.id)),
            }
            for repository in repositories
        ],
    }


def get_repository_releases(repository) -> list:
    """Releases do produto em que o repositório está em `get_release_repositories`, da mais antiga para a mais nova."""
    return [
        release
        for release in Release.objects.filter(product_id=repository.product_id)
        .select_related("product")
        .order_by("start_at", "id")
        if repository.id in {item.id for item in get_release_repositories(release)}
    ]


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


def get_latest_tsqmis(release: Release, repositories_ids: list) -> dict:
    latest = (
        filter_release_window(TSQMI.objects.filter(repository_id__in=repositories_ids), release)
        .order_by("repository_id", "-created_at", "-id")
        .distinct("repository_id")
    )
    return {item.repository_id: item for item in latest}
