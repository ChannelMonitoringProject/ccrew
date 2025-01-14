from datetime import datetime, timedelta
import logging
from collections import defaultdict
import redis
from dash.html import Figure
import plotly.graph_objects as go
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import Session
from ccrew.config import get_config
from ccrew.models.position_reports import BoatPositionReport

config = get_config()
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)


redis_client = redis.Redis(
    host=config.REDIS["host"], port=config.REDIS["port"], db=config.REDIS["db"]
)


def get_arena():
    """
    Convert arena as defined in config to the one used by plot
    """
    arena = config.AIS_STREAM["arena"]
    arena_bounds = {
        "east": arena[0][0][1],
        "west": arena[0][1][1],
        "south": arena[0][1][0],
        "north": arena[0][0][0],
    }
    return arena_bounds


def get_center(arena_bounds):
    """
    get center point of areana_bouns

    :param arena_bounds [TODO:type]: [TODO:description]
    """

    center = {
        "lat": (arena_bounds["north"] + arena_bounds["south"]) / 2,
        "lon": (arena_bounds["west"] + arena_bounds["east"]) / 2,
    }
    return center


def get_state():
    """
    Get all state elements from redis
    """
    ret = []
    state = redis_client.scan_iter("state:*")
    for state_entry_key in state:
        state_entry = redis_client.json().get(state_entry_key)
        ret.append(state_entry)
    return ret


def get_state_boat_position_reports():
    """
    Get BoatPositionReports from redis state
    """
    ret = []
    state = redis_client.scan_iter("state:BoatPositionReport:*")
    for position_report_key in state:
        position_report = redis_client.json().get(position_report_key)
        ret.append(position_report)
    return ret


def to_defaultdict(list_of_dicts):
    """
    helper to convert from list of dicts [{"mmsi":123, ...}, ... ]
    to a dict of lists { "mmsi": [123, ...], "ship_name":["boaty", ...], ... }
    This is how plotly needs those to be

    :param list_of_dicts
    """
    ret = defaultdict(list)
    for d in list_of_dicts:
        for k, v in d.items():
            ret[k].append(v)
    return ret


def get_state_trace():
    boat_position_reports = get_state_boat_position_reports()
    plot_data = to_defaultdict(boat_position_reports)
    ret = go.Scattermapbox(
        name="state_trace",
        lat=plot_data["lat"],
        lon=plot_data["lon"],
        mode="markers+text",
        marker=dict(
            size=12,
        ),
        text=plot_data["ship_name"],
        textposition="top right",
        showlegend=False,
    )
    return ret


def plot_state():
    arena = get_arena()
    center = get_center(arena)
    zoom = 10

    state_trace = get_state_trace()

    fig = go.Figure()
    fig.add_trace(state_trace)

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",  # Use OpenStreetMap as the background
            center=dict(
                lat=center["lat"],
                lon=center["lon"],
            ),
            zoom=zoom,
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


def get_boat_tail_data(
    tracked_boat, latest=datetime.now(), tail_length=timedelta(minutes=60)
):
    earliest = latest - tail_length
    ret = {"lat": [], "lon": [], "time": [], "speed": []}
    with Session(engine) as session:
        query = (
            session.query(
                BoatPositionReport.lat,
                BoatPositionReport.lon,
                BoatPositionReport.server_timestamp,
                BoatPositionReport.sog,
            )
            .filter(
                and_(
                    BoatPositionReport.mmsi == tracked_boat["mmsi"],
                    BoatPositionReport.ship_name == tracked_boat["ship_name"],
                )
            )
            .filter(
                and_(
                    BoatPositionReport.server_timestamp < latest,
                    BoatPositionReport.server_timestamp > earliest,
                )
            )
        )
        result = query.all()
        # list of tuples to dict
        for entry in result:
            ret["lat"].append(entry[0])
            ret["lon"].append(entry[1])
            ret["time"].append(entry[2])
            ret["speed"].append(entry[3])
    return ret
