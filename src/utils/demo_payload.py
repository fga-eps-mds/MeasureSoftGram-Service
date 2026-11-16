"""Entradas determinísticas de demonstração para o pipeline real de cálculo."""

import copy

_PAYLOAD = {
    "github": {
        "metrics": [
            {"name": "total_issues", "value": 10},
            {"name": "resolved_issues", "value": 8},
            {"name": "sum_ci_feedback_times", "value": 300},
            {"name": "total_builds", "value": 5},
        ]
    },
    "sonarqube": {
        "components": [
            {
                "qualifier": "FIL",
                "path": "src/foo.py",
                "measures": [
                    {"metric": "coverage", "value": 80.0},
                    {"metric": "complexity", "value": 5},
                    {"metric": "functions", "value": 10},
                    {"metric": "comment_lines_density", "value": 20.0},
                    {"metric": "duplicated_lines_density", "value": 0.0},
                    {"metric": "ncloc", "value": 100},
                ],
            },
            {
                "qualifier": "FIL",
                "path": "src/bar.py",
                "measures": [
                    {"metric": "coverage", "value": 60.0},
                    {"metric": "complexity", "value": 8},
                    {"metric": "functions", "value": 15},
                    {"metric": "comment_lines_density", "value": 15.0},
                    {"metric": "duplicated_lines_density", "value": 5.0},
                    {"metric": "ncloc", "value": 200},
                ],
            },
            {
                "qualifier": "UTS",
                "path": "tests/foo_test.py",
                "measures": [{"metric": "tests", "value": 5}, {"metric": "test_execution_time", "value": 100}],
            },
            {
                "qualifier": "UTS",
                "path": "tests/bar_test.py",
                "measures": [{"metric": "tests", "value": 3}, {"metric": "test_execution_time", "value": 80}],
            },
            {
                "qualifier": "TRK",
                "path": "",
                "measures": [{"metric": "test_failures", "value": 0}, {"metric": "test_errors", "value": 0}],
            },
        ]
    },
}


def demo_payload(day=0):
    payload = copy.deepcopy(_PAYLOAD)
    for component in payload["sonarqube"]["components"]:
        for measure in component["measures"]:
            if measure["metric"] == "coverage":
                measure["value"] = 50 + (day % 45)
    return payload


def persist_demo_analysis(repository, at, payload):
    """Calcula todas as camadas com o mesmo pipeline e configuração da Action."""
    from entity_trees.services import resolve_release_configuration
    from math_model.services import MathModelServices
    from math_model.utils import parse_release_configuration
    from releases.analyses import resolve_active_release

    release = resolve_active_release(repository, at)
    configuration = resolve_release_configuration(repository.product, release)
    service = MathModelServices(repository, repository.product)
    metrics = service.build_collected_metrics(payload)
    service.collected_at = at
    for metric in metrics:
        metric.created_at = at
    char_keys, subchar_keys, measure_keys = parse_release_configuration({"data": configuration.data})
    measures, values = service.build_calculated_measures(measure_keys, configuration, metrics)
    subchars, subvalues = service.build_calculated_subcharacteristics(subchar_keys, configuration, values)
    chars, charvalues = service.build_calculated_characteristics(char_keys, configuration, subvalues)
    tsqmi = service.build_tsqmi(configuration, charvalues)
    return service.persist_all(metrics, measures, subchars, chars, tsqmi)
