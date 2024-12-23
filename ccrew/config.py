import os
from dotenv import load_dotenv

load_dotenv()

db_name = os.environ.get("POSTGRES_DB")
db_user = os.environ.get("POSTGRES_USER")
db_pass = os.environ.get("POSTGRES_PASSWORD")


class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pass}@localhost/{db_name}"
    CELERY = {
        "broker_url": "redis://localhost",
        "result_backend": "redis://localhost",
        "task_ignore_results": True,
    }
    REDIS = {
        "host": "localhost",
        "port": 6379,
        "db": 1,
    }
    # CELERY_BROKER_URL = "redis://localhost:6379/0"
    # CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    AIS_STREAM = {
        "arena": [[[51.385, 0.909], [50.678, 2.667]]],
        "api_key": os.environ.get("AIS_STREAM_API_KEY"),
        "update_interval": 15,
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
    if environment == "test":
        return TestConfig()
    if environment == "stage":
        return StagingConfig()
    if environment == "prod":
        return ProductionConfig()
    return Config()
