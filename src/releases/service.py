import logging

import numpy as np
from core.transformations import diff, norm_diff
from django.db.models import QuerySet
from releases.analyses import latest_analysis_records

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
    rows = latest_analysis_records(
        CalculatedCharacteristic.objects.filter(repository_id__in=repositories_ids), release, repositories_ids
    ).select_related("repository", "characteristic")
    return get_process_calculated_characteristics_to_list(list(rows))


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

    rp = [planned_characteristic["value"] for planned_characteristic in planned_values]
    rd = _accomplished_vector(planned_values, accomplished_characteristics)
    if rd is None:
        return None

    # norm_diff divide pela norma do planejado: com a meta toda em 0, o resultado seria inf (ou nan), que não
    # cabe no JSON e derrubava o analysis_data da release
    if not np.any(rp):
        logger.warning("The planned values are all zero: the normalized difference is undefined.")
        return None

    return norm_diff(np.array(rp), np.array(rd))


def _accomplished_vector(planned_values, accomplished_characteristics):
    """
    Valores realizados na ordem das características planejadas, ou None (com aviso no log) se
    alguma planejada não foi realizada ou tem valor fora de [0, 1].
    """
    # com nomes repetidos, vale o último, como na busca linear que existia antes
    accomplished_by_name = {
        characteristic["name"]: characteristic["value"] for characteristic in accomplished_characteristics
    }

    rd = []
    for planned_characteristic in planned_values:
        accomplished_value = accomplished_by_name.get(planned_characteristic["name"])

        if accomplished_value is None:
            logger.warning(
                "Planned characteristic %s was not found in the accomplished characteristics.",
                planned_characteristic["name"],
            )
            return None

        if accomplished_value < 0 or accomplished_value > 1:
            logger.warning("Accomplished characteristic value should be between 0 and 1.")
            return None

        rd.append(accomplished_value)

    return rd


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


def get_latest_analysis_values(queryset: QuerySet, release: Release, entity_field: str) -> dict:
    repository_ids = release.product.repositories.values("id")
    latest = latest_analysis_records(queryset, release, repository_ids).select_related(entity_field)
    return {(item.repository_id, getattr(item, entity_field).key): item for item in latest}
