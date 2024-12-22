from ccrew.ingestion.ais_stream import IngestAISStream, State
from ccrew.models import BoatPositionReport


def test_model_to_dict():
    boat = BoatPositionReport(mmsi=1312, ship_name="BOATY      ")
    print(dir(boat))
    print(boat.as_dict())
    assert False


def test_get_boat_position_report_redis_state_key():
    state = State()
    boat = BoatPositionReport()
    key = state.get_boat_redis_key(boat)
    assert key == "state:BoatPositionReport:None-None"

    boat = BoatPositionReport(mmsi=1234)
    key = state.get_boat_redis_key(boat)
    assert key == "state:BoatPositionReport:1234-None"

    boat = BoatPositionReport(mmsi=1312, ship_name="BOATY      ")
    key = state.get_boat_redis_key(boat)
    assert key == "state:BoatPositionReport:1312-BOATY"


def test_update_boat_state(redisdb):
    state = State()
    boat = BoatPositionReport(mmsi=1312, ship_name="BOATY      ")
    state.update_boat(boat)

    assert False


def test_injest_boat_position_report():
    assert False
