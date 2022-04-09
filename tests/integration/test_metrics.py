
def test_pre_config_metric_post(client):

    dict = {
        "pre_config_id": "507f1f77bcf86cd799439011",
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
    assert response.status_code == 200
    assert response.json == 404


def test_wrong_path(client):

    dict = {
        "pre_config_id": "fi2ng9248",
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


def test_invalid_id_post(client):

    dict = {
        "pre_config_id": "fi2ng9248",
        "comment_lines_density": 0.6,
        "complexity": 0.3,
        "coverage": 0.7,
        "duplicated_lines_density": 0.9,
        "files": 0.4,
        "functions": 0.7,
        "ncloc": 0.1,
        "security_rating": 0.85,
        "test_errors": 0.8,
        "test_execution_time": 0.7,
        "test_failures": 0.5,
        "tests": 0.3
    }

    response = client.post("/pre-config-metrics", json=dict)
    assert response.json == 404
    assert response.status_code == 200
