import pytest
import mongoengine as me
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
    "measures": {
        "passed_tests": {},
        "non_complex_file_density": {},
    },
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


def test_create_pre_config_invalid_field_types(client):
    pre_config_one = PreConfig(name="Name one")
    pre_config_one.save()

    params = {
        "name": "Name two",
        "characteristics": [],
        "subcharacteristics": [],
        "measures": [],
    }

    wrong_fields = "'characteristics', 'subcharacteristics', 'measures'"

    with pytest.raises(me.errors.ValidationError) as error:
        client.post("/pre-configs", json=params)

    assert (
        f"ValidationError (PreConfig:None) (Only dictionaries may be used in a DictField: [{wrong_fields}])"
        in str(error.value)
    )


def test_preconfig_wrong_path(client):
    response = client.post(
        "/selecte-pre-config",
        json={},
    )

    assert response.status_code == 404
