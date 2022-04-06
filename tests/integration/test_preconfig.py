import json
from urllib import response
from flask import jsonify

data = ["maintanability"]


def test_preconfig(client):
    response = client.post(
        "/selected-pre-config",
        json=data,
    )
    assert response.status_code == 201


def test_preconfig_wrong_path(client):
    response = client.post(
        "/selecte-pre-config",
        json=data,
    )
    assert response.status_code == 404
