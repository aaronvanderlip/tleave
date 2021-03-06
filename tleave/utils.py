from datetime import datetime, timedelta
from sets import Set
import logging
import transaction

import feedparser
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
import pyramid
from repoze.lru import lru_cache
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import MetaData

from teastrainer import getSchedule
from tleave import models
from tleave.models import DBSession, Base

settings = pyramid.threadlocal.get_current_registry().settings

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '/tmp/cache/data',
    'cache.lock_dir': '/tmp/cache/lock'
}

cache = CacheManager(**parse_cache_config_options(cache_opts))


ROUTES = ['FAIRMNT', 'FITCHBRG', 'NBRYROCK', 'WORCSTER', 'FRANKLIN',
          'GREENBSH', 'HAVRHILL', 'OLCOLONY',
          'LOWELL', 'NEEDHAM', 'PROVSTOU']

FRIENDLYROUTES = {'FAIRMNT': 'Fairmount', 'FITCHBRG': 'Fitchburg',
                  'NBRYROCK': 'Newburyport/Rockport',
                  'WORCSTER': 'Framingham/Worcester',
                  'FRANKLIN': 'Franklin', 'GREENBSH': 'Greenbush',
                  'HAVRHILL': 'Haverhill', 'OLCOLONY': 'Kingston/Plymouth',
                  'LOWELL': 'Lowell',
                  'NEEDHAM': 'Needham', 'PROVSTOU': 'Providence/Stoughton'}

FEEDS = {'FAIRMNT': 1, 'FITCHBRG': 2, 'NBRYROCK': 11,
         'WORCSTER': 4, 'FRANKLIN': 5,
         'GREENBSH': 232, 'HAVRHILL': 7, 'OLCOLONY': 12,
         'LOWELL': 8, 'NEEDHAM': 10, 'PROVSTOU': 14}

DIRECTIONS = ['O', 'I']
TIMING = ['W', 'S', 'U']

LOG = logging.getLogger(__name__)

db_string = 1
metadata = MetaData()


def importAllSchedules():
    print "Dropping tables"
    Base.metadata.drop_all()
    Base.metadata.create_all()
    for route in ROUTES:
        print route
        for direction in DIRECTIONS:
            for timing in TIMING:
                importSchedule(route, direction, timing)


@cache.cache('service_alerts', expire=300)
def get_alerts(route):

    feed = 'http://talerts.com/rssfeed/alertsrss.aspx?%s' % route
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

    print "Creating tables"
    schedulelist = getSchedule(route=route, direction=direction, timing=timing)

    if schedulelist is not None:
        # FIXME it is not really 'time' here is it?
        for name, time in schedulelist.iteritems():
            print name
            station = models.Station('', '', '')
            station.stationname = name
            station.routeorder = time[1]
            station.route = route
            station.direction = direction
            # Timing should be replaced with schedule to make consistent
            station.timing = timing
            print timing
            station.timetable = [
                models.TimeTable(time=stop['time'], train_num=stop['train_num'])
                for stop in parseToDateTime(time[0]
                                            )]
            DBSession.add(station)
            transaction.commit()


def parseToDateTime(timetable):
    """convert time table to list of datetimes, corrected for 24 clock"""
    datetimetable = []
    pm = False
    prev = None
    for stop in timetable:

        try:
            # Just need the hour to calculate
            time = datetime.strptime(stop['time'], '%I:%M')
            if prev is None:
                prev = time

            # Check to see if the 12 hour mark has been passed
            if time < prev and not pm:
                pm = True

            if not pm:
                stop['time'] = time
                datetimetable.append(stop)

            else:
                time = time + timedelta(hours=12)
                # Check to see if adding 12 hours wraps for trains arriving/leaving the next day
                if time < prev:
                    time = time + timedelta(hours=12)
                stop['time'] = time
                datetimetable.append(stop)

            prev = stop['time']
        # Should these be converted to NULL?
        except ValueError:
            stop['time'] = None
            datetimetable.append(stop)

    return datetimetable


@lru_cache(500)
def nextTrain(stationStart, stationEnd, route, timing, direction='I'):
    """ """
    # Needs logic for weekend time and direction
    starttimes = []
    endtimes = []

    try:
        start = DBSession.query(models.Station).filter(
            models.Station.stationname == stationStart).filter(
            models.Station.route == route).filter(
            models.Station.direction == direction).filter(
            models.Station.timing == timing).one()
        end = DBSession.query(models.Station).filter(
            models.Station.stationname == stationEnd).filter(
            models.Station.route == route).filter(
            models.Station.direction == direction).filter(
            models.Station.timing == timing).one()
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
    startindexes = [cleanstarts.index(time) for time in starttimes if time is not None]
    endindexes = [cleanends.index(time) for time in endtimes if time is not None]

    s1 = Set(startindexes)
    s2 = Set(endindexes)

    intersect = s1.intersection(s2)

    idlist = list(intersect)
    idlist.sort()
    startTrainTimes = [(start.timetable[n], end.timetable[n]) for n in idlist]
    results = startTrainTimes
    return results


@cache.cache('determine_direction_results', expire=3600)
def determineDirection(stationStart, stationEnd, route):
    """determines the direction of travel based on start and end station"""
    start = DBSession.query(models.Station).filter(
        models.Station.stationname == stationStart).filter(
        models.Station.route == route).filter(
        models.Station.direction == 'I')
    end = DBSession.query(models.Station).filter(
        models.Station.stationname == stationEnd).filter(
        models.Station.route == route).filter(
        models.Station.direction == 'I')

    if (start.count() and end.count() != 0):
        if start[0].routeorder < end[0].routeorder:
            return 'I'
        else:
            return 'O'
    else:
        return 'O'


def scheduleIntegrity():
    for route in ROUTES:
        stations = DBSession.query(models.Station).filter(models.Station.route == route)
        for station in stations:
            print station
            print len(station.timetable)
