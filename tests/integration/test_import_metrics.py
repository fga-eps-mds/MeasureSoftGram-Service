import json


def test_pre_config_component_post(client):

    f = open(r"tests/data/sonar.json", "r")
    json_file = json.load(f)
    json_test = {"pre_config_id": "624b45ebac582da342adffc3", "components": json_file}

    response = client.post("/pre-config-components", json=json_test)
    assert response.status_code == 200
    assert response.json == 404


def test_wrong_path(client):

    f = open(r"tests/data/zero_cyclomatic_complexity.json", "r")
    json_file = json.load(f)
    json_test = {"pre_config_id": "624b45ebac582da342adffc3", "components": json_file}

    response = client.post("/pre-confi-components", json=json_test)
    assert response.status_code == 404


def test_invalid_id_post(client):

    f = open(
        r"tests/data/fga-eps-mds-2020_2-Projeto-Kokama-Usuario-17-04-2021.json", "r"
    )
    json_file = json.load(f)
    json_test = {"pre_config_id": "624b45e32h", "components": json_file}

    response = client.post("/pre-config-components", json=json_test)

    assert response.json == 404
    assert response.status_code == 200
