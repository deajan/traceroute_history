#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Hosts can be configured in a config file,
Also happens to read smokeping configuration files to populate hosts to probe

"""

__intname__ = 'traceroute_history.user_interface'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.0'
__build__ = '2020050501'

from fastapi import FastAPI, Request
import uvicorn

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import ofunctions

logger = ofunctions.logger_get_logger()

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('targets.html', {'request': request})

#def target_list
#def target_info
#def config
#def groups
#def alerts

if __name__ == '__main__':
    uvicorn.run('user_interface:app', host='127.0.0.1', port=5001, log_level='info', reload=True)