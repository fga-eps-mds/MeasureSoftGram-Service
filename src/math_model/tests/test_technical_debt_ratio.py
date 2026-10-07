"""
Regras da medida technical_debt_ratio (CA1 do épico DOC#41):
min_threshold = 0, max_threshold = 20, gain_interpretation = -1.
"""

import pytest
from resources import calculate_measures

from utils import staticfiles


def _calculate(values):
    result = calculate_measures(
        {
            "measures": [
                {
                    "key": "technical_debt_ratio",
                    "metrics": [{"key": "sqale_debt_ratio", "value": values}],
                }
            ]
        },
        staticfiles.DEFAULT_PRE_CONFIG,
    )
    return result["measures"][0]["value"]


# Sempre 2+ arquivos: o msgram-core desempacota listas de 1 elemento.
@pytest.mark.parametrize(
    "values, expected",
    [
        ([0.0, 0.0], 1.0),
        ([10.0, 10.0], 0.5),
        ([20.0, 20.0], 0.0),
        ([35.0, 35.0], 0.0),
        ([0.0, 20.0], 0.5),
    ],
)
def test_technical_debt_ratio_score(values, expected):
    assert _calculate(values) == pytest.approx(expected)


def test_technical_debt_ratio_in_default_pre_config():
    characteristics = staticfiles.DEFAULT_PRE_CONFIG["characteristics"]
    maintainability = next(c for c in characteristics if c["key"] == "maintainability")
    modifiability = next(s for s in maintainability["subcharacteristics"] if s["key"] == "modifiability")
    measures = {m["key"]: m for m in modifiability["measures"]}

    assert measures["technical_debt_ratio"]["min_threshold"] == 0
    assert measures["technical_debt_ratio"]["max_threshold"] == 20
    assert all(m["weight"] == 25 for m in measures.values())
    assert sum(m["weight"] for m in measures.values()) == 100
