import logging
import websockets
import asyncio
import traceback
import json
from . import parsers
from ccrew.models import BoatPositionReport
from flask import jsonify
from datetime import timedelta
import redis

from ccrew.config import get_config
from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

config = get_config()


class State:
    # TODO this should be managed by redis instead, as alerting and monitoring can use the state too
    boats: list[BoatPositionReport]

    def __init__(self):
        self.boats = []
        self.redis = redis.Redis(host="localhost", port=6379, db=1)

    def get_boat_id(self, boat: BoatPositionReport) -> str:
        boat_id = str(boat.mmsi) + ":" + str(boat.ship_name).strip()
        return boat_id

    def update_boat(self, boat: BoatPositionReport) -> None:
        """Update or boat in state or add if not already there"""
        boat_id = self.get_boat_id(boat)
        # self.redis.hmset(str(boat_id), boat)

        for b in self.boats:
            if (
                b.mmsi is boat.mmsi
                and str(b.ship_name).strip() == str(boat.ship_name).strip()
            ):
                logging.error(f"Updating {jsonify(b)} to {jsonify(boat)}")
                b = boat
                return
        logging.error(f"Adding boat {boat.mmsi} - {boat.ship_name} to state")
        self.boats.append(boat)

    def get_boat(self, mmsi, ship_name) -> BoatPositionReport | None:
        for b in self.boats:
            if b.mmsi is mmsi and str(b.ship_name).strip() == str(ship_name).strip():
                return b
        return None

    def boat_stale(
        self, boat: BoatPositionReport, interval=timedelta(seconds=15)
    ) -> bool:
        logging.error("Checking if boat is stale")
        boat_in_state = self.get_boat(boat.mmsi, boat.ship_name)
        if boat_in_state is None:
            raise ValueError(
                f"boat {boat.mmsi}-{boat.ship_name} not tracked, can't check if stale"
            )
        timestamp = boat.server_timestamp.value
        last_seen = boat_in_state.server_timestamp.value
        logging.error(f"timestamp type: {type(timestamp)}")
        logging.error(f"last_seen type: {type(last_seen)}")
        if timestamp is None or last_seen is None:
            raise ValueError(f"missing timestamp in model")

        if timestamp > last_seen + interval:
            logging.error(f"Boat is stale, need to update")
            return True

        return False


class IngestAISStream(Task):

    def ingest_boat_position_report(self, payload):
        """ingest a position report and update in database
        If boat not in self.state.boats or if boat is state is stale update
        Keyword arguments
        payload -- the content of the position response from ais stream
        """
        model = parsers.parse_position_report(payload)
        boat_in_state = self.state.get_boat(model.mmsi, model.ship_name)
        if boat_in_state is None or self.state.boat_stale(model):
            logging.error("Storing model")
            self.state.update_boat(model)
            with Session(self.engine) as session:
                session.add(model)
                session.commit()

            # if self.update_check(self.state["boats"], model):
            #     logging.info("Storing model")
            #     # with db.SessionLocal() as session:
            #     #     session.add(model)
        logging.info("Ingested")

    def ingest_ais_stream(self, payload):
        if "MessageType" not in payload:
            logging.error("Missing MessageType key in AIS Stream response")
            logging.error(payload)
            return

        message_type = payload["MessageType"]
        if message_type == "PositionReport":
            self.ingest_boat_position_report(payload)
        # elif message_type == "StandardSearchAndRescueAircraftReport":
        #     self.ingest_aircraft_position_report(payload)
        else:
            logging.error(f"cannot handle message type {message_type}")

    async def ais_stream_listener(self):
        api_key = self.config.AIS_STREAM["api_key"]
        arena = self.config.AIS_STREAM["arena"]
        while True:
            logging.info("Connecting to AIS Stream")
            async with websockets.connect(
                "wss://stream.aisstream.io/v0/stream"
            ) as websocket:
                try:
                    subscribe_message = {
                        "APIKey": api_key,
                        "BoundingBoxes": arena,
                        # "FiltersShipMMSI": ["368207620", "367719770", "211476060"], # Optional!
                        "FilterMessageTypes": [
                            "PositionReport",
                            "StandardSearchAndRescueAircraftReport",
                        ],
                    }

                    subscribe_message_json = json.dumps(subscribe_message)
                    await websocket.send(subscribe_message_json)

                    async for message_json in websocket:
                        message = json.loads(message_json)
                        logging.error(" - Message in websocket")
                        logging.error(message)

                        if message == {"error": "Api Key Is Not Valid"}:
                            logging.error(message)
                            exit(-1)
                        self.ingest_ais_stream(message)
                except websockets.ConnectionClosedError as ccerr:
                    await asyncio.sleep(5)
                except Exception as err:
                    logging.error("err")
                    logging.error(err)
                    logging.error(traceback.format_exc())
                    await asyncio.sleep(5)

    def __init__(self):
        self.config = get_config()
        self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

        self.sessions = {}
        self.state = State()

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
