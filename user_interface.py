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
__version__ = '0.2.0'
__build__ = '2020050601'

from fastapi import FastAPI, Request

# Data validation
from pydantic import BaseModel, Field
from typing import List, Optional

import uvicorn

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import traceroute_history
import ofunctions
import psutil

logger = ofunctions.logger_get_logger()

traceroute_history.load_config()
traceroute_history.load_database()
targets = traceroute_history.list_targets(include_tr=True, formatting='web')


class Target(BaseModel):
    name: str = Field(..., description='User friendly name target name', max_length=255)
    address: str = Field(..., description='Address should be a IPv4, IPv6 or a fqdn address', max_length=255)
    groups: Optional[List[str]] = Field(None, description='List of groups')


app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount('/assets', StaticFiles(directory='assets'), name='assets')


def get_system_data():
    try:
        cpu = psutil.cpu_percent()
    except NameError:
        cpu = -1
    try:
        memory = psutil.virtual_memory()._asdict()['percent']
    except NameError:
        memory = -1

    return {
        'cpu': cpu,
        'memory': memory,
        'version': traceroute_history.__version__,
        'ui_version': __version__
    }


@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('targets.html',
                                      {'request': request, 'targets': targets, 'system': get_system_data()})


@app.get('/target/{name}')
async def target_get():
    return

@app.post('/target')
async def target_new(target: Target):
    return target

@app.put('/target/{name}')
async def target_update(target: Target):
    return target

@app.delete('/target/{name}')
async def target_delete(name):
    return traceroute_history.remove_target(name)


#def target_list
#def target_info
#def config
#def groups
#def alerts

if __name__ == '__main__':
    uvicorn.run('user_interface:app', host='127.0.0.1', port=5001, log_level='info', reload=True)
