#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Hosts can be configured in a config file,
Also happens to read smokeping configuration files to populate hosts to probe

"""

import os
import cgi
from flup.server.fcgi import WSGIServer
#from traceroute_hisory import get_last_traceroutes
#from traceroute_history.traceroute_history import get_last_traceroutes
import traceroute_history

def app(environ, start_response):
    form = cgi.FieldStorage(environ['wsgi.input'], environ=environ)

    GET = {}
    # Create dict GET for usual cgi scripts
    args=os.environ.get("QUERY_STRING", '').split('&')
    for arg in args:
        t=arg.split('=')
        if len(t)>1:
            k,v=arg.split('=')
            GET[k]=v

    # Create dict GET from fcgi scripts
    for key in form.keys():
        GET[key] = form.getvalue(key)

    try:
        target = GET['target']
    except KeyError:
        start_response('404 OK', [('Content-Type', 'text/html')])
        return ('No target argument found')


    traceroutes = traceroute_history.get_last_traceroutes(target)
    start_response('200 OK', [('Content-Type', 'text/html')])

    return ('{0}'.format(traceroutes))

#WSGIServer(app, bindAddress='/tmp/fcgi.sock').run()
WSGIServer(app).run()
