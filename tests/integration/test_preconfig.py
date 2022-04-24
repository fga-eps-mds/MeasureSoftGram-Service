from src.model.pre_config import PreConfig

CREATE_PRE_CONFIG_PARAMS = {
    "characteristics": {
        "reliability": {
            "expected_value": 70,
            "weight": 50,
            "subcharacteristics": ["testing_status"],
            "weights": {"testing_status": 100.0},
        },
        "maintainability": {
            "expected_value": 30,
            "weight": 50,
            "subcharacteristics": ["modifiability"],
            "weights": {"modifiability": 100.0},
        },
    },
    "subcharacteristics": {
        "testing_status": {
            "weights": {"passed_tests": 100.0},
            "measures": ["passed_tests"],
        },
        "modifiability": {
            "weights": {"non_complex_file_density": 100.0},
            "measures": ["non_complex_file_density"],
        },
    },
    "measures": ["passed_tests", "non_complex_file_density"],
}


EMPTY_LEVELS_PRE_CONFIG_LEAN_PARAMS = {
    "_id": [""],
    "name": [""],
    "created_at": [""],
}


def test_create_pre_config_success(client):
    params = {"name": "Pre config 1", **CREATE_PRE_CONFIG_PARAMS}

    response = client.post("/pre-configs", json=params)

    response_json = dict(response.json)
    response_json.pop("created_at", None)
    pre_config_id = response_json.pop("_id", None)

    assert response.status_code == 201
    assert response_json == params
    assert PreConfig.objects.with_id(pre_config_id) is not None


def test_create_pre_config_not_unique_name(client):
    pre_config_one = PreConfig(name="Name one")
    pre_config_one.save()

    params = {"name": "Name one", **CREATE_PRE_CONFIG_PARAMS}

    response = client.post("/pre-configs", json=params)

    assert response.status_code == 422
    assert response.json == {"error": "The pre config name is already in use"}


def test_pre_config(client):
    pre_config_one = PreConfig(name="abc", **CREATE_PRE_CONFIG_PARAMS)
    pre_config_one.save()

    response = client.get("/pre-configs")

    assert response.status_code == 200

    all_pre_configs = [x.to_lean_json() for x in PreConfig.objects.all()]

    assert response.json == all_pre_configs


def test_unique_pre_config(client):
    pre_config = PreConfig(name="def", **CREATE_PRE_CONFIG_PARAMS)
    pre_config.save()

    response = client.get(f"/pre-configs/{pre_config.pk}")

    assert response.status_code == 200
    assert response.json == pre_config.to_json()


def test_preconfig_lean_wrong_path(client):
    response = client.get(
        "/pre-config",
        json={},
    )

    assert response.status_code == 404
