from typing import Any
from billiard.einfo import ExceptionInfo
import logging
import websockets
import asyncio
import traceback
import json
from . import parsers
from ccrew.models import BoatPositionReport
from flask import jsonify
from datetime import timedelta, datetime
import redis
from redis.commands.json.path import Path

from ccrew.config import get_config
from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger

config = get_config()

logger = get_task_logger(__name__)


class State:
    """Manages the state (most current reading) of AIS position reports"""

    def __init__(self):
        self.boats = []
        self.redis = redis.Redis(
            host=config.REDIS["host"], port=config.REDIS["port"], db=config.REDIS["db"]
        )

    def get_boat_redis_key(self, boat: BoatPositionReport) -> str:
        """
        get a redis key from a boat position report model


        :param boat: a BoatPositionReport model containing an mmsi and ship_name keys
        :return: a string key in the format "state:BoatPositionReport:<BOAT MMSI>-<SHIP NAME>"
        """
        ret = f"state:BoatPositionReport:{boat.mmsi}-{str(boat.ship_name).strip()}"
        return ret

    def update_boat(self, boat: BoatPositionReport) -> None:
        """Update or boat in state or add if not already there"""
        redis_key = self.get_boat_redis_key(boat)
        entry = boat.as_dict()
        logger.debug(f"Updating state for {entry}")
        self.redis.json().set(redis_key, Path.root_path(), entry)

    def get_boat(self, boat: BoatPositionReport) -> BoatPositionReport | None:
        """
        Get the state entry for the boat, takes the index (mmsi-ship_name)
        find if entry exists in redis database, and return the boat in the state

        :param boat BoatPositionReport: Boat to check (probably latest from AISStream)
        :return: BoatPositionReport in state, or None if not yet tracked in state
        """

        redis_key = self.get_boat_redis_key(boat)
        boat_in_state = self.redis.json().get(redis_key)
        logger.debug(
            f"Got boat position report {redis_key} - {boat_in_state } of type {type(boat_in_state )}"
        )
        if boat_in_state is None:
            return None
        if type(boat_in_state) is not dict:
            raise ValueError(
                f"Unexpected result from redis state, expected dict got {type(boat_in_state )} for {boat_in_state }"
            )
        ret = BoatPositionReport(**boat_in_state)
        # Something funny is happening here, server_timestamp is an isostring in redis
        # liner thinks it is not a datetime in BoatPositionReport
        return ret

    def boat_stale(self, boat: BoatPositionReport, interval=50) -> bool:
        """
        Checks if boat in state is stale (last signal was more then interval ago)

        :param boat: A BoatPositionReport, probably from AISStream
        :param interval integer: time in seconds to consider state being stale, default 60 seconds
        :return: True if BoatPositionReport is older then interval ago, False otherwise
        :raises ValueError: Boat not yet in state (should not happen as we're testing if its in state before testing if its stale
        :raises ValueError: If any of boat, or boat_in_state is missing `server_timestamp` key
        """

        interval = timedelta(seconds=interval)

        logger.debug(f"Checking if boat is stale {boat}, interval: {interval}")
        boat_in_state = self.get_boat(boat)
        if boat_in_state is None:
            raise ValueError(
                f"boat {boat.mmsi}-{boat.ship_name} not tracked, can't check if stale"
            )
        timestamp = boat.server_timestamp
        last_seen = datetime.fromisoformat(boat_in_state.server_timestamp)
        if timestamp is None or last_seen is None:
            raise ValueError(f"missing timestamp in model")

        if type(timestamp) is not datetime or type(last_seen) is not datetime:
            raise ValueError(
                f"expected datetime, got {type(timestamp)} - {timestamp} and {type(last_seen)} - {last_seen}"
            )

        if timestamp > last_seen + interval:
            logger.debug(
                f"Boat {boat.mmsi}-{boat.ship_name} is stale, need to update (last_seen: {last_seen}, current: {timestamp})"
            )
            return True
        else:
            logger.debug(
                f"Boat {boat.mmsi}-{boat.ship_name} is fresh, no need to update (last_seen: {last_seen}, current: {timestamp})"
            )

        return False


class IngestAISStream(Task):
    autoretry_for = (websockets.ConnectionClosedError,)
    retry_backoff = True
    REDIS_TASK_NAME = "ingest.ais-stream"
    REDIS_TASK_CONTROL_KEY = "task:ingest.ais-stream:control"

    def ingest_boat_position_report(self, payload):
        """ingest a position report and update in database
        If boat not in self.state.boats or if boat is state is stale update
        Keyword arguments
        payload -- the content of the position response from ais stream
        """
        model = parsers.parse_position_report(payload)
        boat_in_state = self.state.get_boat(model)
        if boat_in_state is None or self.state.boat_stale(
            model, interval=config.AIS_STREAM["update_interval"]
        ):
            logger.debug(f"Storing model {model}")
            self.state.update_boat(model)
            with Session(self.engine) as session:
                session.add(model)
                session.commit()

    def ingest_ais_stream(self, payload):
        if "MessageType" not in payload:
            logger.error("Missing MessageType key in AIS Stream response")
            logger.error(payload)
            return

        message_type = payload["MessageType"]
        if message_type == "PositionReport":
            self.ingest_boat_position_report(payload)
        # elif message_type == "StandardSearchAndRescueAircraftReport":
        #     self.ingest_aircraft_position_report(payload)
        else:
            logger.error(f"cannot handle message type {message_type}")

    async def ais_stream_listener(self):
        api_key = self.config.AIS_STREAM["api_key"]
        arena = self.config.AIS_STREAM["arena"]
        done = False
        while not done:
            logger.info("Connecting to AIS Stream")
            async with websockets.connect(
                "wss://stream.aisstream.io/v0/stream"
            ) as websocket:
                try:
                    subscribe_message = {
                        "APIKey": api_key,
                        "BoundingBoxes": arena,
                        "FilterMessageTypes": [
                            "PositionReport",
                            "StandardSearchAndRescueAircraftReport",
                        ],
                    }

                    subscribe_message_json = json.dumps(subscribe_message)
                    await websocket.send(subscribe_message_json)

                    async for message_json in websocket:
                        control = self.redis.get(IngestAISStream.REDIS_TASK_CONTROL_KEY)
                        # To do, update state with some life signal (last updated or last database insert)
                        # self.update_state(state="PROCESSING")
                        if control and control.decode("utf-8") == "stop":
                            done = True
                            break

                        message = json.loads(message_json)
                        if message == {"error": "Api Key Is Not Valid"}:
                            logger.error(message)
                            exit(-1)
                        self.ingest_ais_stream(message)
                except websockets.ConnectionClosedError as ccerr:
                    await asyncio.sleep(5)
                except Exception as err:
                    logger.error("err")
                    logger.error(err)
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(5)

    def __init__(self):
        self.config = get_config()
        self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

        self.sessions = {}
        self.state = State()
        self.redis = redis.Redis(
            host=config.REDIS["host"], port=config.REDIS["port"], db=config.REDIS["db"]
        )

    def before_start(
        self,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ):
        pass

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: ExceptionInfo,
    ) -> None:
        logger.error(f"AIS Task failed {exc}")
        # This should probably be done with update_state
        self.redis.set("task:ingest.ais-stream:status", "failed")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    #     def before_start(self, task_id, args, kwargs):
    #         pass
    #
    #     def after_return(
    #         self,
    #         status: Any,
    #         retval: Any,
    #         task_id: str,
    #         args: Tuple[Any, ...],
    #         kwargs: Dict[str, Any],
    #         einfo: ExceptionInfo,
    #     ) -> None:
    #         return super().after_return(status, retval, task_id, args, kwargs, einfo)
    #
    #    def run(self, *args: Any, **kwargs: Any) -> None:
    #        return super().run(*args, **kwargs)
