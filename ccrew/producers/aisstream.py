import os
import asyncio
import logging
import json
import websockets
import traceback
from kafka import KafkaProducer

from ccrew.config import get_config

# from config import get_config

config = get_config()
print(config)
loglevel = os.environ.get("PYTHONLOGLEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, loglevel, logging.INFO))

kafka_bootstrap = [config.KAFKA["bootstrap_servers"]]
# print(f"{kafka_bootstrap}")
producer = KafkaProducer(bootstrap_servers="localhost:9092")

KAFKA_TOPIC = "aisstream"


def queue_item(item):
    logging.info(f"Will queue: {item}")
    producer.send(KAFKA_TOPIC, item)


async def ais_stream_listener():
    api_key = config.AIS_STREAM["api_key"]
    arena = config.AIS_STREAM["arena"]
    done = False
    while not done:
        logging.info("Connecting to AIS Stream")
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
                    # PUT INTO KAFKA QUEUE HERE

                    message = json.loads(message_json)
                    if message == {"error": "Api Key Is Not Valid"}:
                        logging.error(message)
                        exit(-1)
                    queue_item(message)
            except websockets.ConnectionClosedError as ccerr:
                await asyncio.sleep(5)
            except Exception as err:
                logging.error("err")
                logging.error(err)
                logging.error(traceback.format_exc())
                await asyncio.sleep(5)


if __name__ == "__main__":
    print("HIHIHIH")
    logging.info("Starting AISStream Kafka Producer")
    asyncio.run(ais_stream_listener())
    logging.warning("AISStream producer run ended")
