import json
from urllib import response
from flask import jsonify

user_characteristics = ["maintanability"]

data = {"characteristics": user_characteristics, "name": "pre_config_name"}


def test_preconfig(client):
    response = client.post(
        "/pre-configs",
        json=data,
    )
    assert response.status_code == 201


def test_preconfig_wrong_path(client):
    response = client.post(
        "/selecte-pre-config",
        json=data,
    )
    assert response.status_code == 404
