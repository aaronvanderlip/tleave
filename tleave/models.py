import transaction

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import Text 
from sqlalchemy import ForeignKey 
from sqlalchemy import DateTime 

from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import mapper
from sqlalchemy.orm import relation, backref 

from zope.sqlalchemy import ZopeTransactionExtension
from repoze.lru import lru_cache



DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

metadata = MetaData()

class Model(object):
    def __init__(self, name=''):
        self.name = name

models_table = Table(
        'models',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', Unicode(255), unique=True),
        )

models_mapper = mapper(Model, models_table)


class Station (object):

    def __init__(self, stationname, routeorder, direction):
        self.stationname = stationname
        self.routeorder = routeorder
        #need to be fixed when import is fixed
        self.direction = direction

station_table = Table(        
        'station',
        metadata,
        Column('id',Integer, primary_key=True), 
        #need station order
        #need line that it belongs to
        Column('routeorder',Integer),
        Column('stationname',Text),
        Column('route',Text),
        Column('timing',Text, nullable=True),
        Column('direction',Text, nullable=True),

        )
models_mapper = mapper(Station,station_table)

class TimeTable (object):

    def __init__(self, time):
        self.time = time

    @lru_cache(1000)
    def __repr__(self):
        """get a default formatted time string"""
        try:
            time ='         ' + self.time.strftime('%I:%M %p')
        except AttributeError:
            time = '  No Train  '    
        return time

timetable = Table(
        'timetable',
        metadata,
        Column('id',Integer, primary_key=True), 
        Column('station_id',Integer, ForeignKey('station.id')),
        Column('time',DateTime, nullable=True, default=None),
        )

models_mapper = mapper(TimeTable,timetable,properties={    
    'station':relation(Station, backref='timetable', order_by='id')
    }    )
def populate():
    session = DBSession()
    model = Model(name=u'root')
    session.add(model)
    session.flush()
    transaction.commit()

def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    metadata.bind = engine
    metadata.create_all(engine)
    try:
        populate()
    except IntegrityError:
        pass
