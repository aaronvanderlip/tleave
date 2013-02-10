from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy.orm import scoped_session, relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension
from repoze.lru import lru_cache

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()
metadata = MetaData()

class Station (Base):
    __tablename__ = 'station'
    metadata
    id = Column(Integer, primary_key=True)
    #need station order
    #need line that it belongs to
    routeorder = Column(Integer)
    stationname = Column(Text)
    #is this even being used
    route = Column(Text)
    timing = Column(Text, nullable=True)
    direction = Column(Text, nullable=True)
    timetable = relationship("TimeTable")

    def __init__(self, stationname, routeorder, direction):
        self.stationname = stationname
        self.routeorder = routeorder
        #need to be fixed when import is fixed
        self.direction = direction


class TimeTable (Base):
    __tablename__ = 'timetable'

    id = Column(Integer, primary_key=True)
    train_num = Column(Text)
    station_id = Column(Integer, ForeignKey("station.id"))
    train_num = Column(Text)
    time = Column(DateTime, nullable=True)

    def __init__(self, time, train_num):
        self.time = time
        self.train_num = train_num

    @lru_cache(1000)
    def __repr__(self):
        """get a default formatted time string"""
        try:
            time = '         ' + self.time.strftime('%I:%M %p')
        except AttributeError:
            time = '  No Train  '
        return time


