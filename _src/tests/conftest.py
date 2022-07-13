import pytest
from _src.app import create_app
from _src.model.pre_config import PreConfig
from _src.model.metrics_component_tree import MetricsComponentTree


@pytest.fixture()
def app():
    app, _, _ = create_app(is_testing=True)
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield app

    # clean up / reset resources here

    PreConfig.drop_collection()
    MetricsComponentTree.drop_collection()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
