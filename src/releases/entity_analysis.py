"""
Análise por entidade (US21.02): compara os repositórios de um produto em uma
entidade do modelo de qualidade, dentro de uma release.
"""

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from releases.models import Release
from releases.service import get_latest_values_in_release_window
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic

CHARACTERISTIC = "characteristic"
SUBCHARACTERISTIC = "subcharacteristic"
MEASURE = "measure"
METRIC = "metric"

LEVELS = (CHARACTERISTIC, SUBCHARACTERISTIC, MEASURE, METRIC)

SUPPORTED_MODELS = {
    CHARACTERISTIC: SupportedCharacteristic,
    SUBCHARACTERISTIC: SupportedSubCharacteristic,
    MEASURE: SupportedMeasure,
    METRIC: SupportedMetric,
}

CHILD_LEVEL = {
    CHARACTERISTIC: SUBCHARACTERISTIC,
    SUBCHARACTERISTIC: MEASURE,
    MEASURE: METRIC,
}


def get_configured_entities(configuration) -> dict:
    """
    Entidades da pré-configuração por nível, na ordem em que aparecem nela.

    Cada item traz `parent` (a chave da entidade de cima) e, quando a configuração
    define, `weight` e as faixas `min_threshold`/`max_threshold`. Uma entidade que
    aparece sob mais de um pai é listada uma vez por pai.
    """
    entities = {level: [] for level in LEVELS}

    for characteristic in configuration.data["characteristics"]:
        entities[CHARACTERISTIC].append(
            {"key": characteristic["key"], "parent": None, **_config_fields(characteristic)}
        )

        for subcharacteristic in characteristic["subcharacteristics"]:
            entities[SUBCHARACTERISTIC].append(
                {"key": subcharacteristic["key"], "parent": characteristic["key"], **_config_fields(subcharacteristic)}
            )

            for measure in subcharacteristic["measures"]:
                entities[MEASURE].append(
                    {"key": measure["key"], "parent": subcharacteristic["key"], **_config_fields(measure)}
                )

    measures = SupportedMeasure.objects.filter(key__in=[m["key"] for m in entities[MEASURE]]).prefetch_related(
        "metrics"
    )
    metrics_by_measure = {measure.key: [metric.key for metric in measure.metrics.all()] for measure in measures}

    for measure in unique_by_key(entities[MEASURE]):
        for metric_key in metrics_by_measure.get(measure["key"], []):
            entities[METRIC].append({"key": metric_key, "parent": measure["key"]})

    return entities


class MetricWithoutRepositoryValue(Exception):
    """A métrica faz parte da configuração, mas não tem valor no nível do repositório."""


def get_entity_catalog(release: Release, configuration, visible=None) -> dict:
    """
    Lista, por nível, as entidades da configuração com nome (sem repetição).

    No nível métrica entram só as que têm valor no nível do repositório (TASK21.02.03).
    """
    entities = get_configured_entities(configuration)
    repository_level_metrics = get_repository_level_metric_keys(
        release, [item["key"] for item in entities[METRIC]], visible
    )
    catalog = {}

    for level in LEVELS:
        items = unique_by_key(entities[level])
        if level == METRIC:
            items = [item for item in items if item["key"] in repository_level_metrics]
        names = get_entity_names(level, [item["key"] for item in items])
        catalog[level] = [{"key": item["key"], "name": names.get(item["key"], item["key"])} for item in items]

    return catalog


def get_entity_analysis(release: Release, configuration, level: str, key: str, visible=None):
    """
    Valor da entidade em cada repositório da release e a decomposição dela nos filhos.

    Retorna `None` quando a entidade não faz parte da configuração da release e levanta
    `MetricWithoutRepositoryValue` para uma métrica sem valor no nível do repositório.
    """
    entities = get_configured_entities(configuration)
    configured = [item for item in entities[level] if item["key"] == key]

    if not configured:
        return None
    if level == METRIC and key not in get_repository_level_metric_keys(release, [key], visible):
        raise MetricWithoutRepositoryValue(key)

    supported_entity = SUPPORTED_MODELS[level].objects.get(key=key)
    repositories = get_release_repositories(release, visible)
    repositories_ids = [repository.id for repository in repositories]

    values = get_entity_values(level, release, repositories_ids, [key])
    children = _get_children(level, key, entities, release, repositories_ids)

    entity = {"key": supported_entity.key, "name": supported_entity.name}
    if level == METRIC:
        entity["metric_type"] = supported_entity.metric_type

    return {
        "release": {
            "id": release.id,
            "release_name": release.release_name,
            "start_at": release.start_at,
            "end_at": release.end_at,
        },
        "level": level,
        "entity": entity,
        "reference": _get_reference(level, key, release, configured[0]),
        "repositories": [
            {
                "id": repository.id,
                "name": repository.name,
                **serialize_value(values.get((repository.id, key))),
                "children": [
                    {
                        "key": child["key"],
                        "name": child["name"],
                        "weight": child["weight"],
                        **serialize_value(child["values"].get(repository.id)),
                    }
                    for child in children
                ],
            }
            for repository in repositories
        ],
    }


def get_repository_level_metric_keys(release: Release, keys: list, visible=None) -> set:
    """
    Métricas, entre `keys`, gravadas no nível do projeto (`qualifier = "TRK"`) em algum
    repositório da release. As do SonarQube são gravadas por arquivo e ficam de fora: o
    Service não guarda o valor do `baseComponent`, então elas viriam "sem dado" em todos.
    """
    repositories_ids = [repository.id for repository in get_release_repositories(release, visible)]
    return set(
        CollectedMetric.objects.filter(
            metric__key__in=keys,
            qualifier="TRK",
            repository_id__in=repositories_ids,
        )
        .values_list("metric__key", flat=True)
        .distinct()
    )


def get_release_repositories(release: Release, visible=None):
    """
    Repositórios da release, sempre restritos ao produto dela; sem nenhum, todos os do produto.
    Com `visible` (queryset de repositórios), entram só os que o usuário pode ver: quem tem acesso a
    alguns repositórios do produto não recebe nome nem valores dos demais.

    A release pode ter sido criada apontando para repositórios de outro produto, então
    `release.repositories` sozinho vazaria nome e valores de repositórios de fora.
    """
    product_repositories = release.product.repositories.all()
    repositories = product_repositories.filter(releases=release)
    if not repositories.exists():
        repositories = product_repositories
    if visible is not None:
        repositories = repositories.filter(id__in=visible.values("id"))
    return list(repositories.order_by("name", "id"))


def get_entity_values(level: str, release: Release, repositories_ids: list, keys: list) -> dict:
    if level == CHARACTERISTIC:
        queryset = CalculatedCharacteristic.objects.filter(characteristic__key__in=keys)
    elif level == SUBCHARACTERISTIC:
        queryset = CalculatedSubCharacteristic.objects.filter(subcharacteristic__key__in=keys)
    elif level == MEASURE:
        queryset = CalculatedMeasure.objects.filter(measure__key__in=keys)
    else:
        # o valor do repositório é o da métrica no nível do projeto, não o de cada arquivo
        queryset = CollectedMetric.objects.filter(metric__key__in=keys, qualifier="TRK")

    return get_latest_values_in_release_window(queryset.filter(repository_id__in=repositories_ids), release, level)


def _get_children(level: str, key: str, entities: dict, release: Release, repositories_ids: list) -> list:
    child_level = CHILD_LEVEL.get(level)
    if child_level is None:
        return []

    children = unique_by_key([item for item in entities[child_level] if item["parent"] == key])
    children_keys = [child["key"] for child in children]
    names = get_entity_names(child_level, children_keys)
    values = get_entity_values(child_level, release, repositories_ids, children_keys)

    return [
        {
            "key": child["key"],
            "name": names.get(child["key"], child["key"]),
            "weight": child.get("weight"),
            "values": {
                repository_id: value
                for (repository_id, child_key), value in values.items()
                if child_key == child["key"]
            },
        }
        for child in children
    ]


def _get_reference(level: str, key: str, release: Release, configured: dict):
    if level == CHARACTERISTIC:
        goal = release.goal.data.get(key)
        return {"goal": goal / 100} if goal is not None else None

    if level == MEASURE and "min_threshold" in configured and "max_threshold" in configured:
        return {
            "min_threshold": configured["min_threshold"],
            "max_threshold": configured["max_threshold"],
        }

    return None


def get_entity_names(level: str, keys: list) -> dict:
    return dict(SUPPORTED_MODELS[level].objects.filter(key__in=keys).values_list("key", "name"))


def serialize_value(item) -> dict:
    if item is None:
        return {"value": None, "created_at": None}
    return {"value": item.value, "created_at": item.created_at}


def _config_fields(item: dict) -> dict:
    return {field: item[field] for field in ("weight", "min_threshold", "max_threshold") if field in item}


def unique_by_key(items: list) -> list:
    seen = set()
    unique = []
    for item in items:
        if item["key"] not in seen:
            seen.add(item["key"])
            unique.append(item)
    return unique
