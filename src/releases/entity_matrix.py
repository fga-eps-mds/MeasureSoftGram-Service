"""
Mapa de calor da análise por entidade (US21.02, correções do PO de 21/10): o valor
de cada repositório da release em todas as entidades de um nível do modelo, com a
release anterior e a contribuição de cada par repositório × entidade para a
variação do TSQMI do repositório.

Contribuição: o Core agrega cada nível com a norma ponderada
(`calculate_aggregated_weighted_value`: ‖valores × pesos‖ / ‖pesos‖), e não com a
soma ponderada, então "peso × variação" não dá a variação real do TSQMI. A
contribuição de um par é o TSQMI do repositório recalculado com o valor atual da
entidade menos o recalculado com o valor dela na release anterior, mantendo os
demais valores da release e os pesos da configuração da release escolhida.
"""

import numpy as np
from core.transformations import calculate_aggregated_weighted_value

from releases.dashboard import get_latest_tsqmis, serialize_release
from releases.entity_analysis import (
    CHARACTERISTIC,
    LEVELS,
    MEASURE,
    SUBCHARACTERISTIC,
    get_configured_entities,
    get_entity_names,
    get_entity_values,
    get_release_repositories,
    unique_by_key,
)
from releases.models import Release

MATRIX_LEVELS = (CHARACTERISTIC, SUBCHARACTERISTIC, MEASURE)

PARENT_LEVEL = {
    SUBCHARACTERISTIC: CHARACTERISTIC,
    MEASURE: SUBCHARACTERISTIC,
}


def get_previous_release(release: Release):
    """A release do produto imediatamente anterior pelo `start_at`, ou `None` na primeira."""
    return (
        Release.objects.filter(product_id=release.product_id, start_at__lt=release.start_at)
        .order_by("-start_at", "-id")
        .first()
    )


def get_entity_matrix(release: Release, configuration, level: str) -> dict:
    """
    Colunas: as entidades do nível na ordem da configuração, com o caminho até a
    característica. Linhas: os repositórios da release, com o TSQMI e, por entidade,
    o valor na release, o valor na release anterior e a contribuição.
    """
    model = QualityModel(configuration)
    repositories = get_release_repositories(release)
    repositories_ids = [repository.id for repository in repositories]
    previous_release = get_previous_release(release)

    keys = [entity["key"] for entity in model.entities[level]]
    # o recálculo do TSQMI usa os valores da release do nível escolhido até as características
    current = {
        current_level: get_entity_values(current_level, release, repositories_ids, model.keys(current_level))
        for current_level in _levels_up_to_characteristic(level)
    }
    tsqmis = get_latest_tsqmis(release, repositories_ids)

    if previous_release is not None:
        previous = get_entity_values(level, previous_release, repositories_ids, keys)
        previous_tsqmis = get_latest_tsqmis(previous_release, repositories_ids)
    else:
        previous, previous_tsqmis = {}, {}

    rows = []
    for repository in repositories:
        values = {
            current_level: {
                key: item.value for (repository_id, key), item in items.items() if repository_id == repository.id
            }
            for current_level, items in current.items()
        }
        cells = []
        for key in keys:
            value = values[level].get(key)
            previous_item = previous.get((repository.id, key))
            previous_value = previous_item.value if previous_item else None
            cells.append(
                {
                    "key": key,
                    "value": value,
                    "previous_value": previous_value,
                    "contribution": model.contribution(values, level, key, value, previous_value),
                }
            )

        rows.append(
            {
                "id": repository.id,
                "name": repository.name,
                "tsqmi": {
                    "value": _value_of(tsqmis.get(repository.id)),
                    "previous_value": _value_of(previous_tsqmis.get(repository.id)),
                },
                "cells": cells,
            }
        )

    return {
        "release": serialize_release(release),
        "previous_release": serialize_release(previous_release) if previous_release else None,
        "level": level,
        "columns": model.columns(level),
        "repositories": rows,
    }


class QualityModel:
    """Pesos e hierarquia da configuração da release, para montar as colunas e recalcular o TSQMI."""

    def __init__(self, configuration):
        configured = get_configured_entities(configuration) if configuration else {level: [] for level in LEVELS}
        # uma entidade sob mais de um pai vira uma coluna só, no primeiro lugar em que aparece
        self.entities = {level: unique_by_key(configured[level]) for level in MATRIX_LEVELS}
        self.names = {level: get_entity_names(level, self.keys(level)) for level in MATRIX_LEVELS}
        self.by_key = {level: {item["key"]: item for item in self.entities[level]} for level in MATRIX_LEVELS}

        # filhos de cada entidade com o peso de cada um; os pais de cada entidade em todos os lugares em que aparece
        self.children = {CHARACTERISTIC: {}, SUBCHARACTERISTIC: {}}
        self.parents = {SUBCHARACTERISTIC: {}, MEASURE: {}}
        for level, parent_level in PARENT_LEVEL.items():
            for item in configured[level]:
                siblings = self.children[parent_level].setdefault(item["parent"], [])
                if item["key"] not in {key for key, _ in siblings}:
                    siblings.append((item["key"], item.get("weight")))
                self.parents[level].setdefault(item["key"], set()).add(item["parent"])

    def keys(self, level: str) -> list:
        return [item["key"] for item in self.entities[level]]

    def columns(self, level: str) -> list:
        return [
            {**self._describe(level, item["key"]), "path": self._path(level, item)} for item in self.entities[level]
        ]

    def contribution(self, values: dict, level: str, key: str, value, previous_value):
        """Quanto a entidade mudou o TSQMI do repositório desde a release anterior (`None` sem os dois valores)."""
        if value is None or previous_value is None:
            return None
        current = self.recalculate_tsqmi(values, level, key, value)
        previous = self.recalculate_tsqmi(values, level, key, previous_value)
        if current is None or previous is None:
            return None
        return current - previous

    def recalculate_tsqmi(self, values: dict, level: str, key: str, value: float):
        """
        TSQMI recalculado com o Core trocando o valor de uma entidade: os pais dela são
        reagregados até as características, e as outras entidades ficam com o valor da release.
        """
        values = {current_level: dict(items) for current_level, items in values.items()}
        values[level][key] = value
        changed = {key}

        while level in PARENT_LEVEL:
            parent_level = PARENT_LEVEL[level]
            changed = {parent for child in changed for parent in self.parents[level].get(child, ())}
            for parent in changed:
                values[parent_level][parent] = _aggregate(self.children[parent_level].get(parent, []), values[level])
            level = parent_level

        characteristics = [(item["key"], item.get("weight")) for item in self.entities[CHARACTERISTIC]]
        return _aggregate(characteristics, values[CHARACTERISTIC])

    def _describe(self, level: str, key: str) -> dict:
        return {
            "key": key,
            "name": self.names[level].get(key, key),
            "weight": self.by_key[level][key].get("weight"),
        }

    def _path(self, level: str, item: dict) -> list:
        """As entidades de cima, da característica até o pai, com nome e peso."""
        path = []
        while level in PARENT_LEVEL:
            level = PARENT_LEVEL[level]
            item = self.by_key[level][item["parent"]]
            path.insert(0, {"level": level, **self._describe(level, item["key"])})
        return path


def _aggregate(weighted_keys: list, values: dict):
    """Norma ponderada do Core com os filhos que têm valor e peso, como no cálculo do Service."""
    present = [(values[key], weight) for key, weight in weighted_keys if weight and values.get(key) is not None]
    if not present:
        return None
    entity_values, weights = zip(*present)
    return float(calculate_aggregated_weighted_value(np.array(entity_values), np.array(weights)))


def _levels_up_to_characteristic(level: str) -> list:
    levels = [level]
    while levels[-1] in PARENT_LEVEL:
        levels.append(PARENT_LEVEL[levels[-1]])
    return levels


def _value_of(item):
    return item.value if item is not None else None
