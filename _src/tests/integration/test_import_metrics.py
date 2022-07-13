from tests.test_helpers import read_json
from _src.model.pre_config import PreConfig


class DummyResponse:
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
                    "metrics": ["test_success_density"],
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


def test_import_metrics_inexistent_pre_config_id(client):
    json_file = read_json("tests/data/sonar.json")

    data = {
        "pre_config_id": "624b45ebac582da342adffc3",
        "components": json_file,
        "language_extension": "py",
    }

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 404
    assert response.json == {
        "pre_config_id": "There is no pre configurations with ID 624b45ebac582da342adffc3"
    }


def test_import_metrics_invalid_pre_config_id(client):
    json_file = read_json("tests/data/sonar.json")

    data = {
        "pre_config_id": "123abc",
        "components": json_file,
        "language_extension": "py",
    }

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 404
    assert response.json == {"pre_config_id": "123abc is not a valid ID"}


def test_import_metrics_missing_pre_config_metrics(client, mocker):
    json_file = read_json(
        "tests/data/fga-eps-mds-2020_2-Projeto-Kokama-Usuario-17-04-2021.json"
    )

    pre_config = PreConfig(
        name="pre-config-test-1",
        characteristics={"maintainability": {}, "reliability": {}},
        subcharacteristics={"modifiability": {}, "testing_status": {}},
        measures=["non_complex_file_density", "test_builds"],
    ).save()

    mocker.patch("requests.get", return_value=DummyResponse())

    data = {
        "pre_config_id": str(pre_config.pk),
        "components": json_file["components"],
        "language_extension": "py",
    }

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 422
    assert response.json == {
        "__all__": "The metrics in this file are not the expected in the pre config."
        + " Missing metrics: tests, test_execution_time."
    }


def test_import_metrics_success(client, mocker):
    json_file = read_json("tests/data/sonar.json")

    pre_config = PreConfig(
        name="pre-config-test-1",
        characteristics={"maintainability": {}},
        subcharacteristics={"modifiability": {}},
        measures=[
            "non_complex_file_density",
            "commented_file_density",
            "duplication_absense",
        ],
    ).save()

    mocker.patch("requests.get", return_value=DummyResponse())

    data = {
        "pre_config_id": str(pre_config.pk),
        "components": json_file["components"],
        "language_extension": "py",
    }

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 201
    assert response.json == {}
