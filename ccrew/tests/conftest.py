import os
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text
from flask import Flask, Response

from flask_login import UserMixin
import pytest
from pytest_mock_resources import (
    create_postgres_fixture,
    create_redis_fixture,
    RedisConfig,
    PostgresConfig,
)

# from ccrew.core.auth import User
from ccrew.flask_app import create_app
from ccrew.config import get_config
from ccrew.core import db
from ccrew.core.auth import User


os.environ["ENVIRONMENT"] = "test"


def pmr_redis_config():
    return RedisConfig(image="redis/redis-stack")


def pmr_postgres_config():
    return PostgresConfig(
        image="postgis/postgis:17-3.5",
        # host="database",
        username="user",
        password="password",
        root_database="database",
    )


pg = create_postgres_fixture()
redis = create_redis_fixture()


connection_string = f"{pg}"
print("Connection String:", connection_string)
print(dir(pg))


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
def app(pg):
    os.environ["ENVIRONMENT"] = "test"
    config = get_config()
    app = create_app(config)

    with app.app_context() as ctx:
        print(app)
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    # Create DB
    # yield app
    # DROP


@pytest.fixture(scope="session")
def seed_users(app: Flask, pg: Engine):
    with Session(pg) as session:
        # datastore = app.extensions["security"].
        # user: User = user_datastore.create_user(
        #     email="test@example.com", password="password"
        # )

        user = User(email="test@example.com", password="password")
        session.add(user)
        session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "password"},
        follow_redirects=True,
    )
    # response = client.post(
    #     "/login",
    #     data={"email": "test@example.com", "password": "password"},
    #     follow_redirects=True,
    # )
    assert response.status_code == 200
    print(response.data)
    token = response.json["response"]["user"]["authentication_token"]
    ret = {"Authorization": f"Bearer {token}"}
    return ret


@pytest.fixture()
def user(app):
    with app.app_context():
        # existing_user = User.query.filter_by(email="test@example.com").first()
        # if existing_user:
        #     return existing_user
        user_datastore = app.extensions["security"].datastore
        user: User = user_datastore.create_user(
            email="test@example.com", password="password"
        )
        db.session.add(user)
        db.session.commit()
        # dump_table(db.engine, user.)
        return user


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
