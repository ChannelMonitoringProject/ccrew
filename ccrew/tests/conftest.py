import pytest
from ccrew.flask_app import create_app


@pytest.fixture()
def app():
    app = create_app("config.testing")
    app.config.update({"TESTING": True})
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
