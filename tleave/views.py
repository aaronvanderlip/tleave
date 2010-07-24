from tleave.models import DBSession
from tleave.models import Model
from webob.exc import HTTPFound
from repoze.bfg.url import route_url
from repoze.bfg.view import bfg_view
from tleave.utils import importAllSchedules, nextTrain, getTiming, determineDirection,get_alerts, FRIENDLYROUTES,FEEDS
from tleave.models import Station

def my_view(request):
    dbsession = DBSession()
    root = dbsession.query(Model).filter(Model.name==u'root').first()
    return {'root':root, 'project':'tleave'}


def import_schedule(request):
    importAllSchedules()
    return HTTPFound(location = route_url('/', request, pagename='FrontPage'))



def index(request,route='NBRYROCK',stationStart='North Station', stationEnd='Salem',direction='I',timing='W',feed=11,debug='False'):
    """Handle the front-page."""    


    if 'form.submitted' in request.params:
        route = request.params['route']
        stationStart = request.params['stationStart']
        stationEnd = request.params['stationEnd']
        timing = request.params['timing']
        feed = FEEDS[request.params['route']]
    else:   
        timing = getTiming()    

    station = DBSession.query(Station).filter(Station.route==route).filter(Station.direction==direction).filter(Station.timing==timing).order_by(Station.routeorder)
    direction = determineDirection(stationStart,stationEnd,route)
    nexttrain=nextTrain(stationStart,stationEnd,route,timing, direction)
    #had to convert FRIENDLYROUTES to a list of tuples, not sure why you can't pass a dict
    return dict(project='tLeave',stationpages=station,routes=FRIENDLYROUTES.items(),nexttrain=nexttrain, selectedroute=route, stationStart=stationStart, stationEnd=stationEnd,debug=debug, direction=direction, timing=timing, alerts=get_alerts(feed))    


@bfg_view(renderer='json')
def stationlist(request,route='NBRYROCK',direction='O',sortorder='O'):
    """Handle the front-page."""
    route = request.params['route']
    sortorder = request.params['sortorder']

    stations = DBSession.query(Station).filter(Station.route==route).filter(Station.direction==direction).order_by(Station.routeorder)
    #gahh do i have to build a string here?  need better ajax widget that can comprehend lists
    stationlist = [ station.stationname for station in stations]
    if sortorder == 'O':
        stationlist.reverse()
    return stationlist

