"""
Relações e correlações (US21.04): como as características (ou subcaracterísticas)
de um repositório variam juntas ao longo das releases.

Monta a matriz RD do modelo matemático, com uma release por linha e uma entidade
por coluna, e calcula RD_Corr pela função f_sigma do Core (`correlation_function`):
Pearson se todas as colunas forem normais, Spearman se não.
"""

import numpy as np
from core.transformations import correlation_function
from scipy import stats

from characteristics.models import CalculatedCharacteristic
from entity_trees.services import resolve_release_configuration
from releases.dashboard import get_configured_keys, get_repository_releases, serialize_release
from releases.entity_analysis import CHARACTERISTIC, SUBCHARACTERISTIC, get_entity_names
from releases.service import get_latest_values_in_release_window
from subcharacteristics.models import CalculatedSubCharacteristic

LEVELS = (CHARACTERISTIC, SUBCHARACTERISTIC)

MIN_RELEASES = 3

SIGNIFICANCE_LEVEL = 0.05

INSUFFICIENT_RELEASES = "insufficient_releases"
INSUFFICIENT_ENTITIES = "insufficient_entities"


def get_correlation(repository, level: str) -> dict:
    """
    Correlação entre as entidades do nível no repositório, ao longo das releases.

    As entidades são as da configuração da release mais recente. Cada linha de RD é
    uma release em que o repositório tem valor para todas elas (o da última análise
    na janela da release); as demais ficam de fora e são contadas em `excluded_releases`.
    Com menos de 3 releases ou menos de 2 entidades, `pairs` vem vazia e `reason` diz o motivo.
    """
    releases = get_repository_releases(repository)
    configuration = resolve_release_configuration(repository.product, releases[-1]) if releases else None
    keys = get_configured_keys(configuration, level)
    names = get_entity_names(level, keys)
    keys = [key for key in keys if key in names]

    rows = []
    used_releases = []
    for release in releases:
        values = _get_release_values(level, release, repository, keys)
        if keys and all((repository.id, key) in values for key in keys):
            rows.append([values[(repository.id, key)].value for key in keys])
            used_releases.append(release)

    correlation = {
        "repository": {"id": repository.id, "name": repository.name},
        "level": level,
        "entities": [{"key": key, "name": names[key]} for key in keys],
        "releases": [serialize_release(release) for release in used_releases],
        "excluded_releases": len(releases) - len(used_releases),
        "method": None,
        "non_normal": None,
        "critical_value": None,
        "pairs": [],
        "reason": None,
    }

    if len(keys) < 2:
        return {**correlation, "reason": INSUFFICIENT_ENTITIES}
    if len(rows) < MIN_RELEASES:
        return {**correlation, "reason": INSUFFICIENT_RELEASES}

    result = correlation_function(np.array(rows))

    return {
        **correlation,
        "method": result["method"],
        "non_normal": result["normal"].count(False),
        "critical_value": critical_value(len(rows)),
        # triângulo de baixo da matriz: cada entidade com as que vêm antes dela
        "pairs": [_serialize_pair(keys, result, row, column) for row in range(len(keys)) for column in range(row)],
    }


def critical_value(n: int) -> float:
    """|r| a partir do qual o coeficiente é significativo com n releases (teste t bicaudal, nível de 5%)."""
    t = stats.t.ppf(1 - SIGNIFICANCE_LEVEL / 2, n - 2)
    return float(t / np.sqrt(n - 2 + t**2))


def _get_release_values(level: str, release, repository, keys: list) -> dict:
    if level == CHARACTERISTIC:
        # as linhas do fechamento da release (releases/jobs.py) não são análises
        queryset = CalculatedCharacteristic.objects.filter(release__isnull=True, characteristic__key__in=keys)
    else:
        queryset = CalculatedSubCharacteristic.objects.filter(subcharacteristic__key__in=keys)

    return get_latest_values_in_release_window(queryset.filter(repository=repository), release, level)


def _serialize_pair(keys: list, result: dict, row: int, column: int) -> dict:
    p_value = result["p_values"][row][column]
    return {
        "row": keys[row],
        "column": keys[column],
        "coefficient": result["coefficients"][row][column],
        "p_value": p_value,
        "significant": p_value is not None and p_value < SIGNIFICANCE_LEVEL,
    }
