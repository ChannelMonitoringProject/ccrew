from datetime import datetime, timedelta
import logging
from collections import defaultdict
import redis

# from dash.html import Figure
from plotly.graph_objects import Figure
import plotly.graph_objects as go
from sqlalchemy import and_, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from ccrew import models
from ccrew.config import get_config
from ccrew.models.position_reports import BoatPositionReport
from ccrew.models.track import TrackedBoat

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


def get_boat_tracking_options(mmsi, ship_name):
    """
    Gets the tracking config options for a single boat from database
    """

    with Session(engine) as session:
        select_statement = (
            select(TrackedBoat)
            .where(TrackedBoat.mmsi == mmsi)
            .where(TrackedBoat.ship_name == ship_name)
        )
        result = session.execute(select_statement).scalars().first()
        return result


def get_all_boats_tracking_options():
    with Session(engine) as session:  # type: ignore
        select_statement = select(TrackedBoat)
        result = session.execute(select_statement).scalars().all()
        return result


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


def get_boat_route_data(tracked_boat, earliest=None, latest=datetime.now()):
    """Returns data for plotting a route track trace from database
    if no latest provided, defaults to now, if no earliest an hour before latest
    """
    if not earliest:
        earliest = latest - timedelta(minutes=60)
    ret = {"lat": [], "lon": [], "time": [], "speed": []}
    with Session(engine) as session:  # type: ignore
        query = (
            session.query(
                BoatPositionReport.lat,
                BoatPositionReport.lon,
                BoatPositionReport.server_timestamp,
                BoatPositionReport.sog,
            )
            .filter(
                and_(
                    BoatPositionReport.mmsi == tracked_boat.mmsi,
                    BoatPositionReport.ship_name == tracked_boat.ship_name,
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
        for entry in result:
            ret["lat"].append(entry[0])
            ret["lon"].append(entry[1])
            ret["time"].append(entry[2])
            ret["speed"].append(entry[3])
    return ret


def get_boat_route_trace(tracking_entry: models.TrackedBoat, trace_data):
    mmsi = tracking_entry.mmsi
    name = tracking_entry.ship_name

    color = tracking_entry.color or "red"

    ret = go.Scattermapbox(
        lat=trace_data["lat"],
        lon=trace_data["lon"],
        mode="lines",
        line=dict(color=color),
        marker=dict(
            color=color,
            size=15,
        ),
        text=f"{name} - {mmsi}",
        textposition="top right",
        # hoverinfo=f"{ trace_data['time']} - {trace_data['speed']}kt",
        showlegend=True,
    )
    print(ret)
    return ret


def get_map_at(when=datetime.now()):
    """Gets a plot of map at a given time, defaults to now()
    optionally,
    """
    arena = get_arena()
    center = get_center(arena)
    zoom = 10
    fig = go.Figure()
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

    tracked_boats_options = get_all_boats_tracking_options()
    route_traces = []
    for tracked in tracked_boats_options:
        trace_data = get_boat_route_data(tracked_boat=tracked, latest=when)
        trace = get_boat_route_trace(tracked, trace_data)
        route_traces.append(trace)
    fig.add_traces(route_traces)
    return fig
