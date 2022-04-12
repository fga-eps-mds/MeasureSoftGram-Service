from src.model.pre_config import PreConfig

EMPTY_LEVELS_CREATE_PRE_CONFIG_PARAMS = {
    "characteristics": [""],
    "subcharacteristics": [""],
    "measures": [""],
    "characteristics_weights": [""],
    "subcharacteristics_weights": [""],
    "measures_weights": [""],
}


def test_create_pre_config_success(client):
    params = {"name": "Pre config 1", **EMPTY_LEVELS_CREATE_PRE_CONFIG_PARAMS}

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

    params = {"name": "Name one", **EMPTY_LEVELS_CREATE_PRE_CONFIG_PARAMS}

    response = client.post("/pre-configs", json=params)

    assert response.status_code == 422
    assert response.json == {"error": "The pre config name is already in use"}


def test_preconfig_wrong_path(client):
    response = client.post(
        "/selecte-pre-config",
        json={},
    )
    assert response.status_code == 404
