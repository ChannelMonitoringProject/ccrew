import datetime
from .base import Base
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from dataclasses import dataclass, asdict
from ccrew.core import db


@dataclass
class BoatPositionReport(Base):
    __tablename__ = "boat_postion_reports"
    id = Column(Integer, primary_key=True)
    server_timestamp = Column(DateTime)
    time_utc = Column(String)
    mmsi = Column(Integer)
    ship_name = Column(String)
    cog = Column(Float)
    lat = Column(Float)
    lon = Column(Float)
    msg_id = Column(Integer)
    nav_status = Column(Integer)
    pos_accuracy = Column(Boolean)
    raim = Column(Boolean)
    rate_of_turn = Column(Integer)
    repeat_indicator = Column(Integer)
    sog = Column(Float)
    spare = Column(Integer)
    special_manoeuvre_indicator = Column(Integer)
    time_stamp = Column(Integer)
    true_heading = Column(Integer)
    user_id = Column(Integer)
    valid = Column(Boolean)

    def as_dict(self):
        return {
            c.name: (
                getattr(self, c.name)
                if not isinstance(getattr(self, c.name), datetime.datetime)
                else getattr(self, c.name).isoformat()
            )
            for c in self.__table__.columns
        }
