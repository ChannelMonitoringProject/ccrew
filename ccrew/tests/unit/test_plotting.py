from datetime import datetime, timedelta
from plotly.graph_objects import Figure, Scattermapbox
import pytest
from pytest_mock_resources.fixture import postgresql
from redis.commands.json.path import Path
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from pytest_mock_resources import (
    create_redis_fixture,
    RedisConfig,
    create_postgres_fixture,
)
from ccrew.reporting import plotting
from ccrew.models import Base, track
from ccrew.models.position_reports import BoatPositionReport
from ccrew.models.track import TrackedBoat
from ccrew.tests.conftest import dump_table


@pytest.fixture(autouse=True)
def seed(redis, pg):
    Base.metadata.tables["boat_postion_reports"].create(bind=pg)
    Base.metadata.tables["tracked_boats"].create(bind=pg)
    seed_redis(redis)
    seed_database(pg)

    dump_table(pg, "boat_postion_reports")
    dump_table(pg, "tracked_boats")

    yield
    # TODO: Cleanup: This isn't executed before the yield for some reason?
    # Base.metadata.tables["boat_postion_reports"].drop(bind=pg)
    # Base.metadata.tables["tracked_boats"].drop(bind=pg)


@pytest.fixture(scope="session")
def pmr_redis_config():
    return RedisConfig(image="redis/redis-stack")


def seed_redis(redis):
    boat_state_redis_entry = {
        "id": None,
        "server_timestamp": "2025-01-05T17:42:42.302549",
        "time_utc": "2025-01-05 16:42:42.096444364 +0000 UTC",
        "mmsi": 244650331,
        "ship_name": "TRADE NAVIGATOR",
        "cog": 56.8,
        "lat": 51.20706666666667,
        "lon": 1.9903333333333333,
        "msg_id": 1,
        "nav_status": 0,
        "pos_accuracy": True,
        "raim": False,
        "rate_of_turn": 12,
        "repeat_indicator": 0,
        "sog": 11.1,
        "spare": 0,
        "special_manoeuvre_indicator": 0,
        "time_stamp": 35,
        "true_heading": 61,
        "user_id": 244650331,
        "valid": True,
    }
    redis_key = f"state:BoatPositionReport:244650331-TRADE NAVIGATOR"
    redis.json().set(redis_key, Path.root_path(), boat_state_redis_entry)
    entry = redis.json().get(redis_key)


def seed_database(database_engine: Engine):
    boat_position_report_entry = {
        "server_timestamp": "2025-01-05T17:42:42.302549",
        "time_utc": "2025-01-05 16:42:42.096444364 +0000 UTC",
        "mmsi": 244650331,
        "ship_name": "TRADE NAVIGATOR",
        "cog": 56.8,
        "lat": 51.20706666666667,
        "lon": 1.9903333333333333,
        "msg_id": 1,
        "nav_status": 0,
        "pos_accuracy": True,
        "raim": False,
        "rate_of_turn": 12,
        "repeat_indicator": 0,
        "sog": 11.1,
        "spare": 0,
        "special_manoeuvre_indicator": 0,
        "time_stamp": 35,
        "true_heading": 61,
        "user_id": 244650331,
        "valid": True,
    }

    tracked_boat_entry = {
        "mmsi": 244650331,
        "ship_name": "TRADE NAVIGATOR",
        "color": "blue",
        "label": "Trade Navigator",
    }

    with Session(database_engine) as session:
        tracking_entry_a = TrackedBoat(**tracked_boat_entry)
        position_report_a = BoatPositionReport(**boat_position_report_entry)
        session.add(tracking_entry_a)
        session.add(position_report_a)
        session.commit()
    dump_table(database_engine, "boat_postion_reports")
    dump_table(database_engine, "tracked_boats")
    # yield database_engine


def test_redis_seeding(redis):
    # Verify mock database is seeded correctly
    redis_key = f"mockey"
    redis.json().set(redis_key, Path.root_path(), {"testi": "cal"})
    entry = redis.json().get(redis_key)
    assert entry == {"testi": "cal"}

    redis_key = f"state:BoatPositionReport:244650331-TRADE NAVIGATOR"  # Test Mock seeding function works
    # seed_redis(redis)
    expected = {
        "cog": 56.8,
        "id": None,
        "lat": 51.20706666666667,
        "lon": 1.9903333333333333,
        "mmsi": 244650331,
        "msg_id": 1,
        "nav_status": 0,
        "pos_accuracy": True,
        "raim": False,
        "rate_of_turn": 12,
        "repeat_indicator": 0,
        "server_timestamp": "2025-01-05T17:42:42.302549",
        "ship_name": "TRADE NAVIGATOR",
        "sog": 11.1,
        "spare": 0,
        "special_manoeuvre_indicator": 0,
        "time_stamp": 35,
        "time_utc": "2025-01-05 16:42:42.096444364 +0000 UTC",
        "true_heading": 61,
        "user_id": 244650331,
        "valid": True,
    }

    entry = redis.json().get(redis_key)
    assert entry == expected


def test_database_seeding(pg):
    dump_table(pg, "boat_postion_reports")
    dump_table(pg, "tracked_boats")
    with Session(pg) as session:  # type: ignore
        boat_position_report = session.query(BoatPositionReport).all()
        assert len(boat_position_report) == 1
        assert type(boat_position_report[0]) == BoatPositionReport
        assert int(boat_position_report[0].mmsi) == 244650331
        assert str(boat_position_report[0].ship_name) == "TRADE NAVIGATOR"
        assert boat_position_report[0].lat == 51.2070666666667
        assert boat_position_report[0].lon == 1.99033333333333
        assert boat_position_report[0].sog == 11.1

        boat_tracking_options = session.query(TrackedBoat).all()
        assert len(boat_tracking_options) == 1
        assert type(boat_tracking_options[0]) == TrackedBoat
        assert int(boat_tracking_options[0].mmsi) == 244650331
        assert str(boat_tracking_options[0].ship_name) == "TRADE NAVIGATOR"
        assert str(boat_tracking_options[0].color) == "blue"
    dump_table(pg, "boat_postion_reports")
    dump_table(pg, "tracked_boats")


def test_get_state_boat_position_reports_from_redis(redis):
    # seed_redis(redis)
    plotting.redis_client = redis
    state = plotting.get_state_boat_position_reports()
    boat_state = state[0]
    assert boat_state["mmsi"] == 244650331


def test_to_default_dicts():
    dicts = [{"a": 1, "b": 3}, {"a": 1, "b": 2}]
    default_dicts = plotting.to_defaultdict(dicts)
    assert default_dicts == {"a": [1, 1], "b": [3, 2]}


def test_get_state_trace(redis):
    seed_redis(redis)
    plotting.redis_client = redis
    trace = plotting.get_state_trace()

    expected = Scattermapbox(
        {
            "lat": [51.20706666666667],
            "lon": [1.9903333333333333],
            "marker": {"size": 12},
            "mode": "markers+text",
            "name": "state_trace",
            "showlegend": False,
            "text": ["TRADE NAVIGATOR"],
            "textposition": "top right",
        }
    )
    assert trace == expected


def test_plot_state(redis):
    seed_redis(redis)
    plotting.redis_client = redis
    figure = plotting.plot_state()

    expected_data = (
        Scattermapbox(
            {
                "lat": [51.20706666666667],
                "lon": [1.9903333333333333],
                "marker": {"size": 12},
                "mode": "markers+text",
                "name": "state_trace",
                "showlegend": False,
                "text": ["TRADE NAVIGATOR"],
                "textposition": "top right",
            }
        ),
    )
    assert type(figure) == Figure
    assert figure["data"] == expected_data


def test_get_tracking_entry(pg):
    mmsi = 244650331
    ship_name = "TRADE NAVIGATOR"
    plotting.engine = pg
    tracking_entry = plotting.get_boat_tracking_options(mmsi=mmsi, ship_name=ship_name)
    assert type(tracking_entry) == TrackedBoat
    assert tracking_entry.mmsi == 244650331
    assert tracking_entry.ship_name == "TRADE NAVIGATOR"
    assert tracking_entry.label == "Trade Navigator"
    assert tracking_entry.color == "blue"

    tracking_entry = plotting.get_boat_tracking_options(mmsi=mmsi, ship_name="Fake")
    assert tracking_entry == None

    tracking_entry = plotting.get_boat_tracking_options(mmsi=1312, ship_name=ship_name)
    assert tracking_entry == None


def test_get_all_tracked_boats_options(pg):
    plotting.engine = pg
    options = plotting.get_all_boats_tracking_options()
    assert len(options) == 1
    assert type(options[0]) == TrackedBoat


def test_get_boat_tail_trace(pg):
    # seed_database(pg)
    plotting.engine = pg

    tracking_entry = TrackedBoat(
        mmsi=244650331,
        ship_name="TRADE NAVIGATOR",
        color="blue",
        label="Test Label",
    )

    latest = datetime.strptime("2025-01-05T17:43:42.302549", "%Y-%m-%dT%X.%f")
    boat_tail_data = plotting.get_boat_route_data(tracking_entry, latest=latest)

    expected = {
        "lat": [
            51.2070666666667,
        ],
        "lon": [
            1.99033333333333,
        ],
        "speed": [
            11.1,
        ],
        "time": [
            datetime(2025, 1, 5, 17, 42, 42, 302549),
        ],
    }
    assert all(k in boat_tail_data.keys() for k in ["lat", "lon", "speed", "time"])
    assert boat_tail_data == expected

    boat_tail_trace = plotting.get_boat_route_trace(tracking_entry, boat_tail_data)
    expected = Scattermapbox(
        {
            "lat": [51.2070666666667],
            "line": {"color": "blue"},
            "lon": [1.99033333333333],
            "marker": {"color": "blue", "size": 15},
            "mode": "lines",
            "showlegend": True,
            "text": "TRADE NAVIGATOR - 244650331",
            "textposition": "top right",
        }
    )
    assert boat_tail_trace == expected


def test_get_map_at(pg, redis):
    latest = datetime.strptime("2025-01-05T17:43:42.302549", "%Y-%m-%dT%X.%f")
    plotting.engine = pg
    plotting.redis = redis
    plot = plotting.get_map_at(when=latest)
    assert type(plot) == Figure
    # assert plot == {}
