#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Hosts can be configured in a config file,
Also happens to read smokeping configuration files to populate hosts to probe

"""

import os
import sys
import getopt
import cgi
from flup.server.fcgi import WSGIServer

# Make sure we import traceroute_history module that resides in the same path as current fcgi script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from traceroute_history import traceroute_history_runner

GET = {}

# Get command line variables for debugging purposes
try:
    opts, _ = getopt.getopt(sys.argv[1:], '', ['target=', 'limit='])
    for opt, arg in opts:
        if opt == '--target':
            GET['target'] = arg
        if opt == '--limit':
            GET['limit'] = arg
except getopt.GetoptError:
    print('Invlid command line arguments given.')

def app(environ, start_response):
    global GET

    form = cgi.FieldStorage(environ['wsgi.input'], environ=environ)

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

    try:
        limit = GET['limit']
    except KeyError:
        limit = 5

    config = traceroute_history_runner.load_config()
    traceroute_history_runner.load_database(config['TRACEROUTE_HISTORY']['database_host'])
    traceroutes = traceroute_history_runner.get_last_traceroutes_formatted(target, limit, format='web')
    if traceroutes is not None:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ('{0}'.format(traceroutes))

    start_response('404 OK', [('Content-Type', 'text/html')])
    return ('Target has no data.')

WSGIServer(app).run()
