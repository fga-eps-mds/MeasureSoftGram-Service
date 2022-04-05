from flask import jsonify


def test_hello_world(client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.data == b'{"Hello":"World!"}\n'
