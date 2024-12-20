from datetime import datetime
from ccrew.models import BoatPositionReport


def parse_position_report(msg: dict) -> BoatPositionReport:
    """
    Maps an API response to model

    Note: Always index on both mmsi and ship_name.
    MMSI can be shared by different boats sometimes

    :param msg dict: the contents of the AISStream response
    :return: A BoatPositionReport model
    """
    ret = BoatPositionReport(
        **{
            "server_timestamp": datetime.now(),
            "time_utc": msg["MetaData"][
                "time_utc"
            ],  # Should come from AIS Stream but bad format, 9 microseconds
            "mmsi": msg["MetaData"]["MMSI"],
            "ship_name": msg["MetaData"]["ShipName"],
            "cog": msg["Message"]["PositionReport"]["Cog"],
            "lat": msg["Message"]["PositionReport"]["Latitude"],
            "lon": msg["Message"]["PositionReport"]["Longitude"],
            "msg_id": msg["Message"]["PositionReport"]["MessageID"],
            "nav_status": msg["Message"]["PositionReport"]["NavigationalStatus"],
            "pos_accuracy": msg["Message"]["PositionReport"]["PositionAccuracy"],
            "raim": msg["Message"]["PositionReport"]["Raim"],
            "rate_of_turn": msg["Message"]["PositionReport"]["RateOfTurn"],
            "repeat_indicator": msg["Message"]["PositionReport"]["RepeatIndicator"],
            "sog": msg["Message"]["PositionReport"]["Sog"],
            "spare": msg["Message"]["PositionReport"]["Spare"],
            "special_manoeuvre_indicator": msg["Message"]["PositionReport"][
                "SpecialManoeuvreIndicator"
            ],
            "time_stamp": msg["Message"]["PositionReport"]["Timestamp"],
            "true_heading": msg["Message"]["PositionReport"]["TrueHeading"],
            "user_id": msg["Message"]["PositionReport"]["UserID"],
            "valid": msg["Message"]["PositionReport"]["Valid"],
        }
    )
    return ret
