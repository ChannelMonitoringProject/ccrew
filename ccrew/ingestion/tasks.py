from ccrew.celery_app import create_celery_app
from .ais_stream import IngestAISStream
import asyncio
import logging
from ccrew.config import get_config
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

config = get_config()
celery_app = create_celery_app()


@celery_app.task(
    queue="ais-stream", bind=True, base=IngestAISStream, name="ingest.ais-stream"
)
def process_ais_stream(self):
    ingest = IngestAISStream()
    asyncio.run(ingest.ais_stream_listener())
