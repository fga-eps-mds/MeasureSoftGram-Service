from tests.test_helpers import read_json
from src.model.pre_config import PreConfig


def test_import_metrics_inexistent_pre_config_id(client):
    json_file = read_json("tests/data/sonar.json")

    data = {"pre_config_id": "624b45ebac582da342adffc3", "components": json_file}

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 404
    assert response.json == {
        "pre_config_id": "There is no pre configurations with ID 624b45ebac582da342adffc3"
    }


def test_import_metrics_invalid_pre_config_id(client):
    json_file = read_json("tests/data/sonar.json")

    data = {"pre_config_id": "123abc", "components": json_file}

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 404
    assert response.json == {"pre_config_id": "123abc is not a valid ID"}


def test_import_metrics_missing_pre_config_metrics(client):
    json_file = read_json(
        "tests/data/fga-eps-mds-2020_2-Projeto-Kokama-Usuario-17-04-2021.json"
    )

    pre_config = PreConfig(
        name="pre-config-test-1", measures=["non_complex_file_density", "test_builds"]
    ).save()

    data = {"pre_config_id": str(pre_config.pk), "components": json_file}

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 422
    assert response.json == {
        "__all__": "The metrics in this file are not the expected in the pre config."
        + "Missing metrics: tests, test_execution_time."
    }


def test_import_metrics_success(client):
    json_file = read_json(
        "tests/data/fga-eps-mds-2020_2-Projeto-Kokama-Usuario-17-04-2021.json"
    )

    pre_config = PreConfig(
        name="pre-config-test-1",
        measures=[
            "non_complex_file_density",
            "commented_file_density",
            "duplication_absense",
        ],
    ).save()

    data = {"pre_config_id": str(pre_config.pk), "components": json_file}

    response = client.post("/import-metrics", json=data)

    assert response.status_code == 201
    assert response.json == {}
