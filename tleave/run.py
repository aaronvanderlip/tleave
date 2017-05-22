from pyramid.config import Configurator
from pyramid.renderers import JSON
from sqlalchemy import engine_from_config

from tleave.views import stationlist, import_schedule
from tleave.models import (
    DBSession,
    Base,
)


def app(global_config, **settings):
    """ This function returns a WSGI application.

    It is usually called by the PasteDeploy framework during
    ``paster serve``.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.begin()
    config.add_route('home', '/')
    #config.add_route('import', 'import')
    #config.add_view(import_schedule, route_name='import')

    config.add_renderer('stationjson', JSON(indent=4))
    config.add_route('stationlist', 'stationlist/')
    config.add_view(stationlist, route_name='stationlist', renderer='stationjson')

    config.add_static_view('static', 'templates/static')
    config.scan()
    config.end()
    return config.make_wsgi_app()
