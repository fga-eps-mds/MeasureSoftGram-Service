import pytest
from src.app import create_app


@pytest.fixture()
def app():
    app, _, _ = create_app(is_testing=True)
    app.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
