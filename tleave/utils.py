from datetime import datetime, timedelta
from sets import Set
import logging

import transaction

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine
from teastrainer import getSchedule
from tleave import models
from tleave.models import DBSession

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

import feedparser
from repoze.lru import lru_cache


cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '/tmp/cache/data',
    'cache.lock_dir': '/tmp/cache/lock'
}

cache = CacheManager(**parse_cache_config_options(cache_opts))


ROUTES = ['FAIRMNT', 'FITCHBRG', 'NBRYROCK','WORCSTER','FRANKLIN',\
         'GREENBSH','HAVRHILL', 'OLCOLONY'\
         ,'LOWELL','NEEDHAM', 'PROVSTOU']
FRIENDLYROUTES = {'FAIRMNT':'Fairmount', 'FITCHBRG':'Fitchburg',\
                  'NBRYROCK':'Newburyport/Rockport',\
                  'WORCSTER':'Framingham/Worcester',\
                  'FRANKLIN':'Franklin','GREENBSH':'Greenbush',\
                  'HAVRHILL':'Haverhill','OLCOLONY':'Kingston/Plymouth',\
                  'LOWELL':'Lowell',\
                  'NEEDHAM':'Needham','PROVSTOU':'Providence/Stoughton'}


FEEDS = {'FAIRMNT':1, 'FITCHBRG':2, 'NBRYROCK':11,'WORCSTER':4,'FRANKLIN':5,\
        'GREENBSH':232,'HAVRHILL':7, 'OLCOLONY':12\
        ,'LOWELL':8,'NEEDHAM':10, 'PROVSTOU':14}

DIRECTIONS = ['O', 'I']
TIMING = ['W', 'S', 'U']

__all__ = ['setup_app']

LOG = logging.getLogger(__name__)

from sqlalchemy import MetaData
db_string = 'sqlite://///tleave.db'
metadata = MetaData()

def importAllSchedules():
    #print "Dropping tables"
    #repeating ourselves
    engine = create_engine(db_string)
    DBSession.configure(bind=engine)
    metadata.bind = engine


    metadata.drop_all(engine)
    for route in ROUTES:
        for direction in DIRECTIONS:
            for timing in TIMING:
                importSchedule(route,direction,timing)


@cache.cache('service_alerts', expire=300)
def get_alerts(route):
    
    feed =  'http://talerts.com/rssfeed/alertsrss.aspx?%s' % route
    parser = feedparser.parse(feed)
    try:
       results = parser['entries'][0].summary_detail['value']

    except IndexError:
       results = None 

    finally:
       return results       

def getTiming():
    currenttime = datetime.now()     
    timing = 'W'

    if currenttime.isoweekday() == 7:
        timing = 'U'
    if currenttime.isoweekday() == 6:
        timing = 'S'
    return timing

def importSchedule(route, direction, timing):
    """this should go in another library, but its purpose
       is to populate the database"""
    
    #print "Creating tables"

    engine = create_engine(db_string)
    DBSession.configure(bind=engine)
    metadata.bind = engine
    metadata.create_all(engine)
    
    schedulelist = getSchedule(route=route, direction=direction, timing=timing)
    if schedulelist is not None:
        for name,time in schedulelist.iteritems():
            station = models.Station('','','')
            station.stationname = name
            station.routeorder = time[1]
            station.route = route
            station.direction = direction
            #timing should be replaced with schedule to make consistent
            station.timing = timing 
            station.timetable = [models.TimeTable(time = stop) for stop in parseToDateTime(time[0])]
            models.DBSession.add(station)
            transaction.commit()
     

def parseToDateTime(timetable):
    """convert time table to list of datetimes, corrected for 24 clock"""
    datetimetable = []
    pm = False
    prev = None

    for stop in timetable:
        
        try: 
            #just need the hour to calculate
            stop = datetime.strptime(stop, '%I:%M')       
            if prev is None:
                prev = stop 
      
            #check to see if the 12 hour mark has been passed
            if stop < prev and not pm:
                pm = True  
                    
            if not pm:
                datetimetable.append(stop)
                     
            else:        
                stop = stop + timedelta(hours = 12)
                #check to see if adding 12 hours wraps for trains arriving/leaving the next day
                if stop < prev:
                    stop = stop + timedelta(hours = 12)                                    
                datetimetable.append(stop)
                
            prev = stop
        #should these be converted to NULL?    
        except ValueError:
            datetimetable.append(None)
              
    return datetimetable
            

@lru_cache(500)
def nextTrain(stationStart,stationEnd, route, timing, direction='I'):
    """ """
    #needs logic for weekend time and direction
    currenttime = datetime.now()
    now = datetime(year=1900, month=1, day=1, hour=currenttime.hour, minute=currenttime.minute)
    starttimes =[]
    endtimes = []    

    try:
        start = DBSession.query(models.Station).filter(models.Station.stationname==stationStart).filter(models.Station.route==route).filter(models.Station.direction==direction).filter(models.Station.timing==timing).one()
        end = DBSession.query(models.Station).filter(models.Station.stationname==stationEnd).filter(models.Station.route==route).filter(models.Station.direction==direction).filter(models.Station.timing==timing).one()
    except NoResultFound:
        return [] 
    
    # find the times the time table looking forward from now 
    for time in start.timetable:
        try: 
                starttimes.append(time.time)
        except TypeError:
            pass
    
    for time in end.timetable:
        try: 
                endtimes.append(time.time)
        except TypeError:
            pass
    
    # this needs to be refactored 
    # each station has a timetable referenced to it
    cleanstarts = [stop.time for stop in start.timetable]
    cleanends = [stop.time for stop in end.timetable]

    # this creates a list of positional indexes for times in the time tables
    # if the index position matches, there is a train for that destination, this mimicks the rows in the printed schedule
    # this is essentially equivilant to the train number in the printed scheudle
    startindexes = [cleanstarts.index(time) for time in starttimes]
    endindexes = [cleanends.index(time) for time in endtimes]

    s1 = Set(startindexes)
    s2 = Set(endindexes)
    
    intersect = s1.intersection(s2)
    
    idlist = list(intersect)
    idlist.sort()
    startTrainTimes = [(start.timetable[n], end.timetable[n]) for n in idlist]
    results = startTrainTimes 
    return results
    
    
@cache.cache('determine_direction_results', expire=3600)
def determineDirection(stationStart,stationEnd, route): 
    """determines the direction of travel based on start and end station""" 
    start = DBSession.query(models.Station).filter(models.Station.stationname==stationStart).filter(models.Station.route==route).filter(models.Station.direction=='I')
    end = DBSession.query(models.Station).filter(models.Station.stationname==stationEnd).filter(models.Station.route==route).filter(models.Station.direction=='I')


    if (start.count() and  end.count() != 0):
        if start[0].routeorder < end[0].routeorder:
            return 'I'
        else:
            return 'O' 
    else:
        return 'O'


def scheduleIntegrity():
    for route in ROUTES:
        stations = DBSession.query(models.Station).filter(models.Station.route==route)
        for station in stations:
            print station
            print len(station.timetable)

            
