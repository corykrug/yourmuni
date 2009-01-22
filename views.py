from google.appengine.api import users
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from models import *
from forms import *
import google.appengine.ext.db
import nextbus
from shared import userRequired, render_with_user

defaultSource='nb'

def getDefaultSource():
    """return the default source site for user (nextbus for now)"""
    return defaultSource
    
def home(r):    
    user = users.get_current_user()
    if (user):
        q = db.Query(Bmark)
        q.filter('user = ', user)
        bmarks = q.fetch(limit=200)
        links = [ { 'url':'/addbmark', 'title':'add a bookmark' } ]
        param = { 'bmarks': bmarks, 'links': links }
        return render_with_user('user/home.html', param)
    else:
        return render_to_response('splash.html');

def login(r):
    return HttpResponseRedirect(users.create_login_url('/'))

def logout(r):
    return HttpResponseRedirect(users.create_logout_url('/'))
    
@userRequired    
def addBmark(r):
    if (r.method) == 'POST':
        form = AddBmarkForm(r.POST)
        if (form.is_valid()):
            bm = Bmark()
            bm.user = users.get_current_user()
            bm.name = form.cleaned_data['name']
            bm.desc = form.cleaned_data['description']
            bm.put()
            url = '/addstop/'+getDefaultSource()+'/'+bm.name+'/_dflt'
            return HttpResponseRedirect(url)
    else:
        form = AddBmarkForm()
    return render_with_user('user/addbmark.html', {'form':form})
        
@userRequired
def catch(r, bmark):
    q = db.Query(Bmark)
    q.filter('name =', bmark)
    bm = q.get()
    q = db.Query(Stop)
    q.filter('bmark = ', bm)
    stops = []
    error = None
    for row in q:
        stopInfo = nextbus.getTimeURL(row.url)
        if (stopInfo):
            stops.append(stopInfo)
        else:
            error = "Some stops could not be retreived"

    links = [ { 'url':'/nb/addstop/%s/_dflt' % (bmark), 'title':'add a stop' },
              { 'url':'/catch/%s' % bmark, 'title':'reload'}]

    params = {
        'bmark_name': bm.name,
        'bmark_desc': bm.desc,
        'stops': stops,
        'links': links,
        'error': error
    }
    return render_with_user('user/catch.html', params)

@userRequired
def deleteBmark(r, bmark, confirm=None):
    q = db.Query(Bmark)
    q.filter('name = ', bmark)
    q.filter('user = ', users.get_current_user())
    bm = q.get()
    if (bm):
        if (confirm):
            bm.delete()
            return HttpResponseRedirect('/')
        else:
            resource = {
                'type': 'bookmark',
                'desc': bm.desc
            }
            params = {
                'resource' : resource,
                'confirm_url': (r.build_absolute_uri()+'/confirm'),
                'cancel_url': '/'
            }
            return render_with_user('user/delete.html', params)
    else:
        return home(r)
    
@userRequired
def clearCache(r):
    import logging
    from google.appengine.api import memcache
    if users.is_current_user_admin():
        logging.info("Flushing Cache")
        memcache.flush_all()
    return home(r)