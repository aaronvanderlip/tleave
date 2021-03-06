from exceptions import Exception
from pyramid.url import route_url
from pyramid.view import view_config
from pyramid.renderers import render_to_response
from webob.exc import HTTPFound

from tleave.utils import (
    importAllSchedules,
    nextTrain, getTiming,
    determineDirection, get_alerts,
    FRIENDLYROUTES, FEEDS
)
from tleave.models import Station
from tleave.models import DBSession

TIMINGS = [('Weekday', 'W'), ('Saturday', 'S'), ('Sunday', 'U')]


def import_schedule(request):
    importAllSchedules()
    return HTTPFound(location=route_url('/', request, pagename='FrontPage'))


@view_config(route_name='home', renderer='tleave:/templates/station.pt')
def index(request, route='NBRYROCK', stationStart='North Station', stationEnd='Rockport',
         direction='I', timing='W', feed=11, debug='False'):
    """Handle the front-page."""

    try:
        if 'form.submitted' in request.params:
            route = request.params['route']
            stationStart = request.params['stationStart']
            stationEnd = request.params['stationEnd']
            timing = request.params['timing']
            feed = FEEDS[request.params['route']]
        else:
            timing = getTiming()

        station = DBSession.query(Station).filter(
            Station.route == route).filter(
            Station.direction == direction).filter(
            Station.timing == timing).order_by(Station.routeorder)
        direction = determineDirection(stationStart, stationEnd, route)
        nexttrain = nextTrain(stationStart, stationEnd, route, timing, direction)

        schedule = dict(project='tLeave', stationpages=station, routes=FRIENDLYROUTES.items(),
                        nexttrain=nexttrain, selectedroute=route, stationStart=stationStart,
                        stationEnd=stationEnd, debug=debug, direction=direction, timing=(timing),
                        timings=TIMINGS, alerts=get_alerts(feed))
        return schedule

    except Exception:
        return render_to_response('tleave:templates/error.pt', '', request=request)


def stationlist(request, route='NBRYROCK', direction='O', sortorder='O'):
    """Handle the front-page."""
    route = request.params['route']
    sortorder = request.params['sortorder']

    stations = DBSession.query(Station).filter(
        Station.route == route).filter(
        Station.direction == direction).order_by(Station.routeorder)
    # Gahh do i have to build a string here?  need better ajax widget that can comprehend lists
    stationlist = [station.stationname for station in stations]

    if sortorder == 'O':
        stationlist.reverse()
    return stationlist
