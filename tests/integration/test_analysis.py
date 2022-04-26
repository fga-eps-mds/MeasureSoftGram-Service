import json
from tests.test_helpers import read_json
from src.model.metrics_component_tree import MetricsComponentTree
from src.model.analysis import AnalysisComponents
from src.model.pre_config import PreConfig


class AvailableConstantsResponse:
    def json(self):
        return {
            "characteristics": {
                "reliability": {
                    "name": "Reliability",
                    "subcharacteristics": ["testing_status"],
                },
                "maintainability": {
                    "name": "Maintainability",
                    "subcharacteristics": ["modifiability"],
                },
            },
            "subcharacteristics": {
                "testing_status": {
                    "name": "Testing Status",
                    "measures": ["passed_tests", "test_builds", "test_coverage"],
                    "characteristics": ["reliability"],
                },
                "modifiability": {
                    "name": "Modifiability",
                    "measures": [
                        "non_complex_file_density",
                        "commented_file_density",
                        "duplication_absense",
                    ],
                    "characteristics": ["maintainability"],
                },
            },
            "measures": {
                "passed_tests": {
                    "name": "Passed Tests",
                    "subcharacteristics": ["testing_status"],
                    "characteristics": ["reliability"],
                    "metrics": ["tests", "test_errors", "test_failures"],
                },
                "test_builds": {
                    "name": "Test Builds",
                    "subcharacteristics": ["testing_status"],
                    "characteristics": ["reliability"],
                    "metrics": ["tests", "test_execution_time"],
                },
                "test_coverage": {
                    "name": "Test Coverage",
                    "subcharacteristics": ["testing_status"],
                    "characteristics": ["reliability"],
                    "metrics": ["coverage"],
                },
                "non_complex_file_density": {
                    "name": "Non complex file density",
                    "subcharacteristics": ["modifiability"],
                    "characteristics": ["maintainability"],
                    "metrics": ["complexity", "functions"],
                },
                "commented_file_density": {
                    "name": "Commented file density",
                    "subcharacteristics": ["modifiability"],
                    "characteristics": ["maintainability"],
                    "metrics": ["comment_lines_density"],
                },
                "duplication_absense": {
                    "name": "Duplication abscense",
                    "subcharacteristics": ["modifiability"],
                    "characteristics": ["maintainability"],
                    "metrics": ["duplicated_lines_density"],
                },
            },
        }


class AnalysisResultsResponse:
    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
            "sqc": {"sqc": 0.6165241607725739},
            "subcharacteristics": {
                "modifiability": 0.5,
                "testing_status": 0.7142857142857143,
            },
            "characteristics": {
                "maintainability": 0.5,
                "reliability": 0.7142857142857143,
            },
        }


def test_analysis_inexistent_preconfig(client):
    data = {"pre_config_id": "62659019c5e3cb85fcb1e378"}

    response = client.post("/analysis", json=data)

    assert response.status_code == 404
    assert json.loads(response.text) == {
        "error": f"There is no pre configurations with ID {data['pre_config_id']}"
    }


def test_analysis_inexistent_metric_file(client):

    pre_config_without_metrics = PreConfig(
        name="pre-config-test-1",
        characteristics={"maintainability": {}, "reliability": {}},
        subcharacteristics={"modifiability": {}, "testing_status": {}},
        measures=["non_complex_file_density", "test_builds"],
    ).save()

    data = {"pre_config_id": str(pre_config_without_metrics.pk)}

    response = client.post("/analysis", json=data)

    assert response.status_code == 404
    assert json.loads(response.text) == {
        "error": f"There is no metrics file associated with this pre config {data['pre_config_id']}"
    }


def test_analysis_already_exists(client, mocker):

    json_file = read_json("tests/data/sonar.json")

    pre_config = PreConfig(
        name="pre-config-test-2",
        characteristics={
            "reliability": {
                "expected_value": 70,
                "weight": 50,
                "subcharacteristics": ["testing_status"],
                "weights": {"testing_status": 100},
            },
            "maintainability": {
                "expected_value": 30,
                "weight": 50,
                "subcharacteristics": ["modifiability"],
                "weights": {"modifiability": 100},
            },
        },
        subcharacteristics={
            "modifiability": {
                "weights": {"non_complex_file_density": 100},
                "measures": ["non_complex_file_density"],
            },
            "testing_status": {
                "weights": {"passed_tests": 100},
                "measures": ["passed_tests"],
            },
        },
        measures=["passed_tests", "non_complex_file_density"],
    ).save()

    pre_configuration_id = pre_config.to_json()["_id"]

    json_file = read_json("tests/data/sonar.json")

    mocker.patch("requests.get", return_value=AvailableConstantsResponse())

    components = MetricsComponentTree(
        pre_config_id=pre_configuration_id,
        components=json_file["components"],
        language_extension="py",
    ).save()

    AnalysisComponents(
        pre_config_id=pre_configuration_id,
        sqc={"sqc": 0.769309258162072},
        aggregated_scs={"modifiability": 0.42857142857142855, "testing_status": 1},
        aggregated_characteristics={
            "maintainability": 0.42857142857142855,
            "reliability": 1,
        },
    ).save()

    data = {"pre_config_id": pre_configuration_id}

    response = client.post("/analysis", json=data)

    analysis_values = {
        "sqc": {"sqc": 0.769309258162072},
        "subcharacteristics": {
            "modifiability": 0.42857142857142855,
            "testing_status": 1,
        },
        "characteristics": {
            "maintainability": 0.42857142857142855,
            "reliability": 1,
        },
    }

    assert response.status_code == 200
    assert response.json == {
        "pre_config": pre_config.to_json(),
        "components": components.to_json(),
        "analysis": analysis_values,
    }


def test_analysis_success(client, mocker):
    pre_config = PreConfig(
        name="pre-config-test-2",
        characteristics={
            "reliability": {
                "expected_value": 70,
                "weight": 50,
                "subcharacteristics": ["testing_status"],
                "weights": {"testing_status": 100},
            },
            "maintainability": {
                "expected_value": 30,
                "weight": 50,
                "subcharacteristics": ["modifiability"],
                "weights": {"modifiability": 100},
            },
        },
        subcharacteristics={
            "modifiability": {
                "weights": {"non_complex_file_density": 100},
                "measures": ["non_complex_file_density"],
            },
            "testing_status": {
                "weights": {"passed_tests": 100},
                "measures": ["passed_tests"],
            },
        },
        measures=["passed_tests", "non_complex_file_density"],
    ).save()

    pre_configuration_id = pre_config.to_json()["_id"]

    json_file = read_json("tests/data/sonar.json")

    mocker.patch("requests.get", return_value=AvailableConstantsResponse())

    components = MetricsComponentTree(
        pre_config_id=pre_configuration_id,
        components=json_file["components"],
        language_extension="py",
    ).save()

    data = {"pre_config_id": pre_configuration_id}

    mocker.patch("requests.post", return_value=AnalysisResultsResponse())

    response = client.post("/analysis", json=data)

    analysis_values = {
        "sqc": {"sqc": 0.6165241607725739},
        "subcharacteristics": {
            "modifiability": 0.5,
            "testing_status": 0.7142857142857143,
        },
        "characteristics": {
            "maintainability": 0.5,
            "reliability": 0.7142857142857143,
        },
    }

    assert response.status_code == 201
    assert response.json == {
        "pre_config": pre_config.to_json(),
        "components": components.to_json(),
        "analysis": analysis_values,
    }
