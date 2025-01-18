from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

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


def dump_table(engine: Engine, table_name: str):
    """
    Dumps the contents of the specified table using a SQLAlchemy engine.

    Args:
        engine (Engine): The SQLAlchemy engine connected to the database.
        table_name (str): The name of the table to dump.

    Returns:
        List[Dict]: A list of rows in the table, each represented as a dictionary.
    """
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT * FROM {table_name}"))
        rows = [dict(row) for row in result.mappings()]

    # Print table contents for debugging
    print(f"Contents of table '{table_name}':")
    for row in rows:
        print(row)

    return rows


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
