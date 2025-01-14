import pytest
from pytest_mock_resources import (
    create_postgres_fixture,
    create_redis_fixture,
    RedisConfig,
)

from ccrew.flask_app import create_app


def pmr_redis_config():
    return RedisConfig(image="redis/redis-stack")


pg = create_postgres_fixture()
redis = create_redis_fixture()


@pytest.fixture()
def app():
    app = create_app(config.testing)
    app.config.update({"TESTING": True})
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}
    app.config["SECURITY_PASSWORD_HASH"] = "plaintext"
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
