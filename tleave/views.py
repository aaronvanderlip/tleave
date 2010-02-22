from tleave.models import DBSession
from tleave.models import Model
from webob.exc import HTTPFound
from repoze.bfg.url import route_url

from tleave.utils import importAllSchedules, nextTrain, getTiming, determineDirection, FRIENDLYROUTES
from tleave.models import Station

def my_view(request):
    dbsession = DBSession()
    root = dbsession.query(Model).filter(Model.name==u'root').first()
    return {'root':root, 'project':'tleave'}


def import_schedule(request):
    importAllSchedules()
    return HTTPFound(location = route_url('import_schedule', request, pagename='FrontPage'))

def index(request,foobar='NBRYROCK',stationStart='North Station', stationEnd='Salem',direction='I',timing='W',debug='False'):
    """Handle the front-page."""    
    timing = getTiming()   
    station = DBSession.query(Station).filter(Station.route==foobar).filter(Station.direction==direction).filter(Station.timing==timing).order_by(Station.routeorder)
    direction = determineDirection(stationStart,stationEnd,foobar)
    nexttrain=nextTrain(stationStart,stationEnd,foobar,timing, direction)
    #had to convert FRIENDLYROUTES to a list of tuples, not sure why you can't pass a dict
    return dict(project='tLeave',stationpages=station,routes=FRIENDLYROUTES.items(),nexttrain=nexttrain, selectedroute=foobar, stationStart=stationStart, stationEnd=stationEnd,debug=debug, direction=direction, timing=timing)    
