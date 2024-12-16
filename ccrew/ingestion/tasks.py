from ccrew.celery_app import create_celery_app
from .ais_stream import IngestAISStream
import asyncio
import logging
from ccrew.config import get_config

config = get_config()
celery = create_celery_app()


@celery.task(queue="ais-stream")
def process_ais_stream():
    ingest = IngestAISStream()
    asyncio.run(ingest.ais_stream_listener())
