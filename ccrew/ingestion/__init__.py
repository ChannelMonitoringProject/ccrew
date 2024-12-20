import logging
from flask import Blueprint
from . import tasks
from .tasks import celery, process_ais_stream

# from ccrew.celery_app import celery

# It's cleaner to stop celery tasks using redis control entry
ais_stream_task_id = None
ais_stream_task_response = None
ingestion_bp = Blueprint("ingestion", __name__)


def ais_stream_running():
    task_name = "ccrew.ingestion.tasks.process_ais_stream"
    inspector = tasks.celery.control().inspect()
    active_tasks = inspector.active()
    if not active_tasks:
        return False
    return True


@ingestion_bp.route("/ais/status")
def ingestion_status():
    return {}


@ingestion_bp.route("/ais/start")
def start_ais():
    global ais_stream_task_id
    if ais_stream_task_id:
        logging.warning(f"Task id {ais_stream_task_id} already running")
        return {"message": f"Task {ais_stream_task_id} was already running"}

    ais_stream_task_response = process_ais_stream.delay()
    logging.info(ais_stream_task_response)
    return {
        "message": "starting AIS Stream listener task",
        "task-id": ais_stream_task_response.task_id,
    }


@ingestion_bp.route("/ais/stop")
def stop_ais():
    if ais_stream_task_response:
        ais_stream_task_response.revoke(terminate=True)
    # global ais_stream_task_id
    # if ais_stream_task_id is None:
    #     logging.warning(f"AIS Stream listener not running")
    #     return {"message": f"Task not running"}
    # celery.control().revoke(ais_stream_task_id, terminate=True)
    # ais_stream_task_id = None
    return {}
