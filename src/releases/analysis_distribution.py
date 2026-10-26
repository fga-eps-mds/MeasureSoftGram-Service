"""
Distribuição estatística (US21.03): como os valores de uma entidade do modelo se
espalham entre as análises de um repositório na release.

Cada análise é uma execução da coleta: MathModelServices.persist_all grava uma
linha por entidade e por repositório. A série de cada entidade é lida sozinha,
sem ligar as camadas pela data, então os dados antigos (em que as camadas da
mesma análise têm instantes um pouco diferentes) entram sem tolerância.
"""

from statistics import fmean, quantiles, stdev

from rest_framework import serializers

from characteristics.models import CalculatedCharacteristic
from measures.models import CalculatedMeasure
from metrics.models import CollectedMetric
from releases.entity_analysis import (
    CHARACTERISTIC,
    CHILD_LEVEL,
    MEASURE,
    METRIC,
    SUBCHARACTERISTIC,
    SUPPORTED_MODELS,
    MetricWithoutRepositoryValue,
    get_configured_entities,
    get_repository_level_metric_keys,
    unique_by_key,
)
from releases.service import filter_release_window
from subcharacteristics.models import CalculatedSubCharacteristic
from tsqmi.models import TSQMI

TSQMI_LEVEL = "tsqmi"

LEVELS = (TSQMI_LEVEL, CHARACTERISTIC, SUBCHARACTERISTIC, MEASURE, METRIC)

TSQMI_ENTITY = {"key": TSQMI_LEVEL, "name": "TSQMI", "metric_type": None}


class EntityNotConfigured(Exception):
    """A entidade não faz parte da configuração da release."""


def summarize(values):
    """
    Resumo estatístico dos valores das análises.

    Quartis e percentis pelo método `inclusive`, o mesmo do QUARTIL.INC e do
    PERCENTIL.INC das planilhas. A assimetria é a amostral ajustada, a mesma do
    DISTORÇÃO, e fica `None` com menos de 3 análises ou com desvio zero.
    """
    if not values:
        return {
            "count": 0,
            **dict.fromkeys(("min", "p10", "q1", "median", "q3", "p90", "max", "iqr", "lower_limit", "upper_limit")),
            "outliers": 0,
            "mean": None,
            "skewness": None,
        }

    ordered = sorted(values)
    if len(ordered) == 1:
        # `quantiles` exige pelo menos dois valores
        p10 = q1 = median = q3 = p90 = ordered[0]
    else:
        q1, median, q3 = quantiles(ordered, n=4, method="inclusive")
        deciles = quantiles(ordered, n=10, method="inclusive")
        p10, p90 = deciles[0], deciles[-1]

    iqr = q3 - q1
    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr

    return {
        "count": len(ordered),
        "min": ordered[0],
        "p10": p10,
        "q1": q1,
        "median": median,
        "q3": q3,
        "p90": p90,
        "max": ordered[-1],
        "iqr": iqr,
        "lower_limit": lower_limit,
        "upper_limit": upper_limit,
        "outliers": sum(1 for value in ordered if value < lower_limit or value > upper_limit),
        "mean": fmean(ordered),
        "skewness": skewness(ordered),
    }


def skewness(values):
    """Assimetria amostral ajustada: n / ((n-1)(n-2)) · Σ((x - média) / s)³, com s amostral."""
    n = len(values)
    if n < 3:
        return None

    deviation = stdev(values)
    if deviation == 0:
        return None

    mean = fmean(values)
    return n / ((n - 1) * (n - 2)) * sum(((value - mean) / deviation) ** 3 for value in values)


def get_analysis_distribution(release, repository, configuration, level: str, key: str = None) -> dict:
    """
    Análises da entidade e dos filhos dela no repositório, dentro da janela da release.

    Levanta `EntityNotConfigured` para uma entidade fora da configuração da release e
    `MetricWithoutRepositoryValue` para uma métrica sem valor por análise (só as
    gravadas com `qualifier = "TRK"` têm um valor por análise).
    """
    entities = get_configured_entities(configuration) if configuration else None

    if level == TSQMI_LEVEL:
        entity = TSQMI_ENTITY
        children_level = CHARACTERISTIC
        children = unique_by_key(entities[CHARACTERISTIC]) if entities else []
    else:
        if entities is None or not any(item["key"] == key for item in entities[level]):
            raise EntityNotConfigured(key)
        if level == METRIC and key not in get_repository_level_metric_keys(release, [key]):
            raise MetricWithoutRepositoryValue(key)

        entity = _get_supported_entities(level, [key])[key]
        children_level = CHILD_LEVEL.get(level)
        children = (
            unique_by_key([item for item in entities[children_level] if item["parent"] == key])
            if children_level
            else []
        )

    entity_series = _get_series(level, repository, release, [entity["key"]]).get(entity["key"], [])

    serialized_children = []
    if children:
        children_keys = [child["key"] for child in children]
        children_series = _get_series(children_level, repository, release, children_keys)
        supported_children = _get_supported_entities(children_level, children_keys)
        # na ordem da configuração; filhos sem valor por análise ficam fora
        serialized_children = [
            _serialize_entity(children_level, supported_children[child_key], children_series[child_key])
            for child_key in children_keys
            if children_series.get(child_key) and child_key in supported_children
        ]

    return {
        "release": {
            "id": release.id,
            "release_name": release.release_name,
            "start_at": local_datetime(release.start_at),
            "end_at": local_datetime(release.end_at),
        },
        "repository": {"id": repository.id, "name": repository.name},
        "level": level,
        "key": entity["key"],
        "period": {
            "count": len(entity_series),
            "first": local_datetime(entity_series[0][0]) if entity_series else None,
            "last": local_datetime(entity_series[-1][0]) if entity_series else None,
        },
        "entity": _serialize_entity(level, entity, entity_series),
        "children": serialized_children,
    }


def _get_series(level: str, repository, release, keys: list) -> dict:
    """Análises (created_at, valor) de cada entidade em `keys`, ordenadas por data."""
    if level == TSQMI_LEVEL:
        rows = (
            filter_release_window(TSQMI.objects.filter(repository=repository), release)
            .order_by("created_at", "id")
            .values_list("created_at", "value")
        )
        return {TSQMI_LEVEL: list(rows)}

    if level == CHARACTERISTIC:
        # as linhas do fechamento da release (releases/jobs.py) não são análises
        queryset = CalculatedCharacteristic.objects.filter(release__isnull=True)
    elif level == SUBCHARACTERISTIC:
        queryset = CalculatedSubCharacteristic.objects.all()
    elif level == MEASURE:
        queryset = CalculatedMeasure.objects.all()
    else:
        # as métricas do SonarQube são gravadas por arquivo e não têm valor por análise
        queryset = CollectedMetric.objects.filter(qualifier="TRK")

    key_field = f"{level}__key"
    rows = (
        filter_release_window(queryset.filter(repository=repository, **{f"{key_field}__in": keys}), release)
        .order_by("created_at", "id")
        .values_list(key_field, "created_at", "value")
    )

    series = {}
    for entity_key, created_at, value in rows:
        series.setdefault(entity_key, []).append((created_at, value))
    return series


def _get_supported_entities(level: str, keys: list) -> dict:
    fields = ("key", "name", "metric_type") if level == METRIC else ("key", "name")
    return {
        item["key"]: {"metric_type": None, **item}
        for item in SUPPORTED_MODELS[level].objects.filter(key__in=keys).values(*fields)
    }


def _serialize_entity(level: str, entity: dict, series: list) -> dict:
    summary = summarize([value for _, value in series])
    lower_limit, upper_limit = summary["lower_limit"], summary["upper_limit"]

    return {
        "key": entity["key"],
        "name": entity["name"],
        "level": level,
        "metric_type": entity["metric_type"],
        "analyses": [
            {
                "date": local_datetime(created_at),
                "value": value,
                "is_outlier": value < lower_limit or value > upper_limit,
            }
            for created_at, value in series
        ],
        "summary": summary,
    }


def local_datetime(value):
    return serializers.DateTimeField().to_representation(value) if value else None
