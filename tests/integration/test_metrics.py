from pyexpat import model
import json


def test_pre_config_metric_post(client):

    dict = {
        "id_wanted": "fi2ng9248",
        "comment_lines_density": 0.2,
        "complexity": 0.5,
        "coverage": 0.2,
        "duplicated_lines_density": 0.3,
        "files": 0.8,
        "functions": 0.5,
        "ncloc": 0.9,
        "security_rating": 0.1,
        "test_errors": 0.2,
        "test_execution_time": 0.1,
        "test_failures": 0.3,
        "tests": 0.2
    }

    response = client.post("/pre-config-metrics", json=dict)
    message = '{"metrics_list": {"comment_lines_density": 0.2, "complexity": 0.5, "coverage": 0.2, "duplicated_lines_density": 0.3, "files": 0.8, "functions": 0.5, "ncloc": 0.9, "security_rating": 0.1, "test_errors": 0.2, "test_execution_time": 0.1, "test_failures": 0.3, "tests": 0.2}' + '}\n'
    byte_message = bytes(message, 'utf-8')
    print(response.data)
    print("\n\n")
    print(byte_message)
    assert response.status_code == 201
    assert response.data == byte_message

def test_wrong_path(client):

    dict = {
        "id_wanted": "fi2ng9248",
        "comment_lines_density": 0.2,
        "complexity": 0.5,
        "coverage": 0.2,
        "duplicated_lines_density": 0.3,
        "files": 0.8,
        "functions": 0.5,
        "ncloc": 0.9,
        "security_rating": 0.1,
        "test_errors": 0.2,
        "test_execution_time": 0.1,
        "test_failures": 0.3,
        "tests": 0.2
    }

    response = client.post("/pre-config-etrics", json=dict)
    assert response.status_code == 404

def test_wrong_file_post(client):

    dict = {
        "id_wanted": "fi2ng9248",
        "comment_lines_density": 0.2,
        "complexity": 0.5,
        "coverage": 0.2,
        "duplicated_lines_density": 0.3,
        "files": 0.8,
        "functions": 0.5,
        "ncloc": 0.9,
        "security_rating": 0.1,
        "test_errors": 0.2,
        "test_execution_time": 0.1,
        "test_failures": 0.3,
        "tests": 0.2
    }

    response = client.post("/pre-config-metrics", data=dict)
    assert response.status_code == 400

def test_invalid_id(client):

    dict = {
        "id_wanted": None,
        "comment_lines_density": 0.2,
        "complexity": 0.5,
        "coverage": 0.2,
        "duplicated_lines_density": 0.3,
        "files": 0.8,
        "functions": 0.5,
        "ncloc": 0.9,
        "security_rating": 0.1,
        "test_errors": 0.2,
        "test_execution_time": 0.1,
        "test_failures": 0.3,
        "tests": 0.2
    }

    response = client.post("/pre-config-metrics", data=dict)
    assert response.status_code == 400

def test_unsaved_id(client):

    dict = {
        "id_wanted": "id_não_existente",
        "comment_lines_density": 0.2,
        "complexity": 0.5,
        "coverage": 0.2,
        "duplicated_lines_density": 0.3,
        "files": 0.8,
        "functions": 0.5,
        "ncloc": 0.9,
        "security_rating": 0.1,
        "test_errors": 0.2,
        "test_execution_time": 0.1,
        "test_failures": 0.3,
        "tests": 0.2
    }

    response = client.post("/pre-config-metrics", data=dict)
    assert response.status_code == 400
    