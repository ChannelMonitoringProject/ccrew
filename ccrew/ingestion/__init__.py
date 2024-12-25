import inspect
import logging
from flask import Blueprint
from . import tasks
from .tasks import celery_app, process_ais_stream
from .ais_stream import IngestAISStream
from ccrew.config import get_config
import redis
from celery.result import AsyncResult


# from ccrew.celery_app import celery

# It's cleaner to stop celery tasks using redis control entry
ais_stream_task_id = None
ais_stream_task_response = None
ingestion_bp = Blueprint("ingestion", __name__)

config = get_config()

redis_client = redis.Redis(
    host=config.REDIS["host"], port=config.REDIS["port"], db=config.REDIS["db"]
)


def get_active_ais_stream_tasks():
    ret = []
    inspector = tasks.celery_app.control.inspect()
    active_tasks = inspector.active()
    if not active_tasks:
        return
    for worker, ts in active_tasks.items():
        for t in ts:
            if t["name"] == IngestAISStream.REDIS_TASK_NAME:
                ret.append(t)
    return ret


@ingestion_bp.route("/ais/status")
def ingestion_status():
    ret = {}
    active_ais_stream_tasks = get_active_ais_stream_tasks()
    if not active_ais_stream_tasks:
        return {
            "message": "No active AIS Stream ingestion tasks, use /start endpoint to start"
        }
    for t in active_ais_stream_tasks:
        result: AsyncResult = AsyncResult(t["id"], app=tasks.celery_app)
        print(result.info)
        print(result.result)

        logging.info(f"Running AIS Stream Task {t} with status {result.status}")
        ret[t["id"]] = {
            "status": result.status,
            "state": result.state,
            "name": t["name"],
        }
    return ret


@ingestion_bp.route("/ais/start")
def start_ais():

    active_ais_stream_tasks = get_active_ais_stream_tasks()
    if not active_ais_stream_tasks:
        redis_client.set(IngestAISStream.REDIS_TASK_CONTROL_KEY, "start")

        ais_stream_task_response = process_ais_stream.delay()
        logging.info(ais_stream_task_response)
        return {
            "message": "starting AIS Stream listener task",
            "task-id": ais_stream_task_response.task_id,
        }
    logging.warning(f"Task already running, not starting a new instance")
    return {"message": f"Task  was already running"}


@ingestion_bp.route("/ais/stop")
def stop_ais():
    logging.warning("AIS Ingestion process stopping, will not monitor AIS Stream")
    redis_client.set(IngestAISStream.REDIS_TASK_CONTROL_KEY, "stop")
    return {"message": "ending ais stream ingestion task"}
