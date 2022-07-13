import pytest
import mongoengine as me
from _src.model.pre_config import PreConfig

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


def test_pre_configs_list(client):
    PreConfig.objects.delete()

    pre_config_one = PreConfig(name="preconfig1").save()
    pre_config_two = PreConfig(name="preconfig2").save()
    pre_config_three = PreConfig(name="preconfig3").save()

    response = client.get("/pre-configs")

    assert response.status_code == 200

    all_pre_configs = [
        pre_config_one.to_lean_json(),
        pre_config_two.to_lean_json(),
        pre_config_three.to_lean_json(),
    ]

    assert response.json == all_pre_configs


def test_create_pre_config_invalid_field_types(client):
    params = {
        "name": "Name two",
        "characteristics": [],
        "subcharacteristics": [],
        "measures": {},
    }

    with pytest.raises(me.errors.ValidationError) as error:
        client.post("/pre-configs", json=params)

    expected_msg = (
        "ValidationError (PreConfig:None) (Only dictionaries may be used in a DictField: "
        + "['characteristics', 'subcharacteristics'] Only lists and tuples may be used in a list field: ['measures'])"
    )

    assert expected_msg in str(error.value)


def test_pre_config_show_success(client):
    pre_config = PreConfig(name="def", **CREATE_PRE_CONFIG_PARAMS)
    pre_config.save()

    response = client.get(f"/pre-configs/{pre_config.pk}")

    assert response.status_code == 200
    assert response.json == pre_config.to_json()


def test_pre_config_show_error(client):
    response = client.get("/pre-configs/123")

    assert response.status_code == 404
    assert response.json["error"] == "123 is not a valid ID"


def test_update_pre_config_name_success(client):
    pre_config = PreConfig(name="To change name")
    pre_config.save()

    response = client.patch(
        f"/pre-configs/{str(pre_config.pk)}", json={"name": "Changed name"}
    )

    assert response.status_code == 200
    assert response.json["name"] == "Changed name"


def test_update_pre_config_name_not_unique(client):
    PreConfig(name="Name").save()

    pre_config = PreConfig(name="Try to change")
    pre_config.save()

    response = client.patch(f"/pre-configs/{str(pre_config.pk)}", json={"name": "Name"})

    assert response.status_code == 422
    assert response.json["error"] == "The pre config name is already in use"


def test_update_pre_config_validation_error(client):
    pre_config = PreConfig()
    pre_config.save()

    params = {
        "characteristics": [],
        "subcharacteristics": [],
        "measures": {},
    }

    response = client.patch(f"/pre-configs/{pre_config.pk}", json=params)

    expected_error_msg = (
        f"ValidationError (PreConfig:{pre_config.pk}) (Only dictionaries may be used in a DictField: "
        + "['characteristics', 'subcharacteristics'] Only lists and tuples may be used in a list field: ['measures'])"
    )

    # I've tested it in Insomnia and it returns correctly
    assert response.status_code == 422
    assert response.json["error"] == expected_error_msg


@pytest.mark.parametrize(
    "pre_config_id,expected_msg",
    [
        ("123", "123 is not a valid ID"),
        (
            "6261b76c974ddbc76bdea7a0",
            "There is no pre configurations with ID 6261b76c974ddbc76bdea7a0",
        ),
    ],
)
def test_update_pre_config_name_invalid_id(client, pre_config_id, expected_msg):
    response = client.patch(f"/pre-configs/{pre_config_id}", json={"name": "Name"})

    assert response.status_code == 404
    assert response.json["error"] == expected_msg


def test_preconfig_wrong_path(client):
    response = client.post(
        "/selecte-pre-config",
        json={},
    )

    assert response.status_code == 404
