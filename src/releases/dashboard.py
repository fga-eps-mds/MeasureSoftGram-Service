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


def get_product_tsqmi_release_history(product, repositories: list) -> dict:
    """
    Histórico do TSQMI por release (US06.01): um ponto por release para cada
    repositório, com a variação em relação à release anterior do mesmo repositório.

    Entram as releases do produto em que o repositório está em `get_release_repositories`,
    da mais antiga para a mais nova. Sem release cadastrada, `releases` vem vazia e cada
    repositório vem com `history` vazio (empty state do Front).
    """
    releases = list(Release.objects.filter(product_id=product.id).select_related("product").order_by("start_at", "id"))
    repositories_ids = {repository.id for repository in repositories}

    releases_by_repository = {repository.id: [] for repository in repositories}
    tsqmis_by_release = {}
    for release in releases:
        release_repositories_ids = [
            repository.id for repository in get_release_repositories(release) if repository.id in repositories_ids
        ]
        for repository_id in release_repositories_ids:
            releases_by_repository[repository_id].append(release)
        tsqmis_by_release[release.id] = get_latest_tsqmis(release, release_repositories_ids)

    return {
        "releases": [serialize_release(release) for release in releases],
        "repositories": [
            {
                "id": repository.id,
                "name": repository.name,
                "history": _get_tsqmi_history(repository, releases_by_repository[repository.id], tsqmis_by_release),
            }
            for repository in repositories
        ],
    }


def _get_tsqmi_history(repository, releases: list, tsqmis_by_release: dict) -> list:
    history = []
    previous_value = None
    for release in releases:
        tsqmi = tsqmis_by_release[release.id].get(repository.id)
        value = serialize_value(tsqmi)
        history.append(
            {
                "release_id": release.id,
                **value,
                **_get_variation(previous_value, value["value"]),
            }
        )
        previous_value = value["value"]
    return history


def _get_variation(previous_value, value) -> dict:
    """
    Variação em relação à release imediatamente anterior. Sem valor numa das duas
    (primeira release ou release sem análise), a variação vem `None`; com a anterior
    igual a zero, só a variação percentual vem `None`.
    """
    if previous_value is None or value is None:
        return {"previous_value": previous_value, "variation": None, "variation_percent": None}
    variation = value - previous_value
    return {
        "previous_value": previous_value,
        "variation": variation,
        "variation_percent": variation / previous_value * 100 if previous_value else None,
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
