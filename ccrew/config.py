import os
from dotenv import load_dotenv

load_dotenv()

db_name = os.environ.get("POSTGRES_DB")
db_user = os.environ.get("POSTGRES_USER")
db_pass = os.environ.get("POSTGRES_PASSWORD")


class Config:
    # Base config, assumedatabase and redis are accessible on localhost.
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pass}@localhost/{db_name}"

    # Redis server for celery tasks, db 0
    CELERY = {
        "broker_url": "redis://localhost",
        "result_backend": "redis://localhost",
        "task_ignore_results": True,
    }
    # Redis server for application level (can be same as celery's host), db 1
    REDIS = {
        "host": "localhost",
        "port": 6379,
        "db": 1,
    }

    # KAFKA Broker
    KAFKA = {
        "bootstrap_servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    }

    AIS_STREAM = {
        "arena": [[[51.385, 0.909], [50.678, 2.667]]],
        "api_key": os.environ.get("AIS_STREAM_API_KEY"),
        # update database/state when last stamp was older then
        "update_interval": 300,
    }

    # For Flask-Security-Too
    # Seed first user
    # Make sure those are defined in ,env
    ADMIN_USER = os.environ.get("ADMIN_USER")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
    SECRET_KEY = os.environ.get("SECRET_KEY", "security key <keep secret>")
    SECURITY_PASSWORD_SALT = os.environ.get(
        "SECURITY_PASSWORD_SALT", "security password salt <keep secret>"
    )
    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DockerConfig(Config):
    # Running dockerised, services are on hosts "redis", "database", etc
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pass}@database/{db_name}"
    CELERY = {
        "broker_url": "redis://redis",
        "result_backend": "redis://redis",
        "task_ignore_results": True,
    }
    REDIS = {
        "host": "redis",
        "port": 6379,
        "db": 1,
    }
    # KAFKA Broker
    KAFKA = {
        "bootstrap_servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    }


class DevelopmentConfig(Config):
    pass


class TestConfig(Config):
    pass


class StagingConfig(Config):
    pass


class ProductionConfig(Config):
    pass


def get_config():
    environment = os.environ.get("ENVIRONMENT", "default")
    if environment == "dev":
        return DevelopmentConfig()
    if environment == "docker":
        return DockerConfig()
    if environment == "test":
        return TestConfig()
    if environment == "stage":
        return StagingConfig()
    if environment == "prod":
        return ProductionConfig()
    return Config()
