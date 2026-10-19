"""
Substituto provisório da medida `technical_debt_ratio` enquanto o Service
usa um msgram-core que ainda não a implementa (< 1.5.5).

A medida segue a mesma lógica de `absence_of_duplications` (percentual por
arquivo, interpolação linear, gain_interpretation = -1), então o cálculo é
delegado a ela trocando a métrica `duplicated_lines_density` por
`sqale_debt_ratio`.

Não faz nada se o msgram-core instalado já conhecer a medida.
REMOVER quando o Service for atualizado para o msgram-core >= 1.5.5.
"""

from core.aggregated_normalized_measures import absence_of_duplications
from core.schemas import DuplicationAbsenceSchema
from marshmallow import ValidationError
from resources.constants import AGGREGATED_NORMALIZED_MEASURES_MAPPING
from staticfiles import SUPPORTED_MEASURES
from util import Checker  # util do core

MEASURE_KEY = "technical_debt_ratio"
METRIC_KEY = "sqale_debt_ratio"


def _technical_debt_ratio(data_frame, min_threshold: float = 0, max_threshold: float = 20):
    return absence_of_duplications(
        {"duplicated_lines_density": data_frame[METRIC_KEY]},
        min_threshold=min_threshold,
        max_threshold=max_threshold,
    )


class _TechnicalDebtRatioSchema(DuplicationAbsenceSchema):
    @staticmethod
    def validate_metrics(metrics):
        for metric in metrics:
            if metric["key"] not in [METRIC_KEY]:
                raise ValidationError(f"'{metric['key']}': Métrica não presente na medida")


def apply():
    if MEASURE_KEY in AGGREGATED_NORMALIZED_MEASURES_MAPPING:
        return

    AGGREGATED_NORMALIZED_MEASURES_MAPPING[MEASURE_KEY] = {
        "aggregated_normalized_measure": _technical_debt_ratio,
        "schema": _TechnicalDebtRatioSchema,
    }

    if not any(MEASURE_KEY in measure for measure in SUPPORTED_MEASURES):
        SUPPORTED_MEASURES.append({MEASURE_KEY: {"metrics": [METRIC_KEY]}})

    if not hasattr(Checker, f"check_{MEASURE_KEY}_threshold"):
        setattr(
            Checker,
            f"check_{MEASURE_KEY}_threshold",
            staticmethod(Checker.check_absence_of_duplications_threshold),
        )
