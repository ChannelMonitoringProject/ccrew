from kombu import Queue
from celery import Celery
from .config import get_config

config = get_config()


def create_celery_app(config=config) -> Celery:
    app = Celery("ccrew")
    app.config_from_object(config.CELERY)

    # AIS Stream has it's own dedicated queue as it's a persistent task
    app.conf.task_queues = (Queue("default"), Queue("ais-stream", routing_key="ais.#"))
    app.conf.task_routes = {
        "ccrew.ingestion.tasks.process_ais_stream": {"queue": "ais_stream"},
    }
    app.autodiscover_tasks(["ccrew.ingestion"], force=True)

    return app


celery = create_celery_app()
