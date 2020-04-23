#! /usr/bin/env python
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Hosts can be configured in a config file,
Also happens to read smokeping configuration files to populate hosts to probe

"""

import cgi
from flup.server.fcgi import WSGIServer

def app(environ, start_response):
    remote = cgi.FieldStorage(environ['wsgi.input'], environ=environ)

    name = 'Doe'
    if 'name' in remote:
        name = remote.get_first('name')

    start_response('200 OK', [('Content-Type', 'text/html')])

    return ('Hello. Your name is %s' % (cgi.escape(name)))


#WSGIServer(app, bindAddress='/tmp/fcgi.sock').run()
WSGIServer(app).run()