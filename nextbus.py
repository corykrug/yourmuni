from views import userRequired, render_with_user
from django.http import HttpResponseRedirect
from lib import nextbus
import google.appengine.ext.db as db
from models import Bmark, Stop
import logging

defaultRegion='California-Northern'
defaultAgency='sf-muni'


def getDefaultRegion():
    """return the default region for user (norcal for now)"""
    return defaultRegion

def getDefaultAgency():
    """return the default agency for the user (sf-muni for now)"""
    return defaultAgency



@userRequired 
def addStop(r, bmark, re=None, agency=None, route=None, 
                                                    direction=None, stop=None):
    error = ''
    if (stop is not None):
        url = nextbus.timeURL % (agency, route, direction, stop)
        q = db.Query(Bmark)
        q.filter('name = ', bmark)
        b = q.get()
        q = db.Query(Stop)
        q.filter('bmark = ', b)
        q.filter('url = ', url)
        stopObj = q.get()
        logging.info(stopObj)
        if (stopObj):
            logging.info("Stop Already Exists")
            error = "This stop has already been added"
        else:
            stopObj = Stop()
            stopObj.bmark = b
            stopObj.url = url
            stopObj.system = "nextbus"
            stopObj.put()
            #TODO: redirect to an edit page that doesnt involve the scrape
            return HttpResponseRedirect('/catch/%s' % (bmark))
    if (direction is not None):
        data = nextbus.getStops(agency, route, direction)
        prefix = '/addstop/nb/%s/%s/%s/%s/%s'\
            % (bmark, re, agency, route, direction)
        subtitle = 'pick a stop'
    elif (route is not None):
        data = nextbus.getDirections(agency, route)
        prefix = '/addstop/nb/%s/%s/%s/%s' % (bmark, re, agency, route)
        subtitle = 'pick a direction'
    elif (agency is not None):
        data = nextbus.getRoutes(agency)
        prefix = '/addstop/nb/%s/%s/%s' % (bmark, re, agency)
        subtitle = 'pick a route'
    items = []
    if not (data):
        #todo: throw 500
        return False
    for key, value in data:
        items.append({'url_piece': key, 'title': value})
    params = { 'items':items,
               'prefix': prefix,
               'subtitle': subtitle,
               'error': error }
    return render_with_user('listoflinks.html', params)

@userRequired
def addStopDflt(r, bmark):
    return addStop(r, bmark, getDefaultRegion(), getDefaultAgency())
