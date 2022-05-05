#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Traceroute History user interface and API

"""

__intname__ = 'traceroute_history.user_interface'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.5.12-dev'
__build__ = '2022050501'


import sys
import os
import getopt
from typing import List
from fastapi import Depends, FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psutil
import ofunctions.logger_utils
from traceroute_history.database import load_database, get_db
from traceroute_history.traceroute_history_runner import config_management, schemas, crud
from traceroute_history import traceroute_history_runner

logger = ofunctions.logger_utils.logger_get_logger()


# TODO: because of get_db that must be initialized before everything, this is a bit of spaghetti code
# best way to deal with it is to move config file and database loading to a module that needs to be called at the begin of code

# Default config file
CONFIG_FILE = 'traceroute_history.conf'
config = None


def help_():
    print('{} {} {}'.format(__intname__, __version__, __build__))
    print('{} under {}'.format(__copyright__, __licence__))
    print('')
    print('Usage:')
    print('{} [options]'.format(__file__))
    print('')
    print('Options:')
    print('')
    print(
        '--config=                            Path to config file. If none given, traceroute_history.conf in the current directory is tried.')
    sys.exit()


def cmd_opts(argv):
    global CONFIG_FILE
    global config_file_set

    try:
        opts, _ = getopt.getopt(argv, "h?",
                                ['config=', 'help'])
    except getopt.GetoptError:
        help_()
        sys.exit(9)

    config_file_set = False
    for opt, arg in opts:
        if opt == '--config':
            CONFIG_FILE = arg
            config_file_set = True

cmd_opts(sys.argv[1:])

# Reload config before executing anything else
config = config_management.load_config(CONFIG_FILE)
try:
    log_file = config['TRACEROUTE_HISTORY']['log_file']
    logger = ofunctions.logger_utils.logger_get_logger(log_file=log_file)
except KeyError:
    pass

if not config_file_set:
    logger.info('No config file set. trying default one: {0}.'.format(os.path.abspath(CONFIG_FILE)))

logger.info('Running with database: {0}.'.format(config['TRACEROUTE_HISTORY']['database_host']))

# Server variables
try:
    bind_to = config['UI_SETTINGS']['bind_to']
except KeyError:
    bind_to = '127.0.0.1'
    logger.info("Could not read bind address. Using default {}".format(bind_to))
try:
    bind_port = int(config['UI_SETTINGS']['bind_port'])
except KeyError:
    bind_port = 5001
    logger.info("Could not read bind port. Using default {}".format(bind_port))

try:
   sub_directory = config['UI_SETTINGS']['sub_directory']
except KeyError:
    sub_directory = ""

# Load database, needs to be done before accessing db_get function
#config = config_management.load_config('traceroute_history.conf')
db_load_result = load_database(config)

# Prepare FastAPI
app = FastAPI()

templates_path = os.path.join(config['TRACEROUTE_HISTORY']['install_dir'], 'traceroute_history', 'www', 'templates')
assets_path = os.path.join(config['TRACEROUTE_HISTORY']['install_dir'], 'traceroute_history', 'www', 'assets')

templates = Jinja2Templates(directory=templates_path)
app.mount('/assets', StaticFiles(directory=assets_path), name='assets')


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
        'version': traceroute_history_runner.__version__,
        'ui_version': __version__,
    }


"""
Main API functions
These aren't async since SQLAlchemy does not support async yet


"""
@app.post('/target/', response_model=schemas.Target)
def create_target(target: schemas.TargetCreate, db: Session = Depends(get_db)):
    db_target = crud.get_target(db=db, name=target.name)
    if db_target:
        raise HTTPException(status_code=400, detail='Target already exists')
    return crud.create_target(db=db, target=target)

@app.get('/targets/', response_model=List[schemas.Target])
def read_targets(skip: int = 0, limit : int = None, db: Session = Depends(get_db)):
    targets = crud.get_targets(db=db, skip=skip, limit=limit)
    return targets

@app.get('/target/{id}', response_model=schemas.Target)
def read_target_by_id(id: int, db: Session = Depends(get_db)):
    db_target = crud.get_target(db=db, id=id)
    if db_target is None:
        raise HTTPException(status_code=404, detail='Target does not exist')
    return db_target

@app.get('/target/name/{name}', response_model=schemas.Target)
def read_target_by_name(name: str, db: Session = Depends(get_db)):
    db_target = crud.get_target(db=db, name=name)
    if db_target is None:
        raise HTTPException(status_code=404, detail='Target does not exist')
    return db_target

@app.delete('/target/{id}')
def delete_traceroute_by_id(id: int, db: Session = Depends(get_db)):
    db_operation = crud.delete_target(db=db, id=id)
    if db_operation is not None:
        raise HTTPException(status_code=404, detail='Target does not exist')
    # deletes return HTTP 200 'null' on success
    return db_operation

@app.delete('/target/name/{name}')
def delete_traceroute_by_name(name: str, db: Session = Depends(get_db)):
    db_operation = crud.delete_target(db=db, name=name)
    if db_operation is not None:
        raise HTTPException(status_code=404, detail='Target does not exist')
    return db_operation


@app.post('/group', response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = crud.get_group(db=db, name=group.name)
    if db_group:
        raise HTTPException(status_code=400, detail='Group already exists')
    return crud.create_group(db=db, group=group)


@app.get('/groups', response_model=List[schemas.Group])
def read_groups(skip: int = 0, limit: int = None, db: Session = Depends(get_db)):
    groups = crud.get_groups(db=db, skip=skip, limit=limit)
    return groups

@app.get('/group/{id}', response_model=schemas.Group)
def read_groupby_id(id: int, db: Session = Depends(get_db)):
    db_group = crud.get_group(db=db, id=id)
    if db_group is None:
        raise HTTPException(status_code=404, detail='Group does not exist')
    return db_group

@app.post('/target/{id}/traceroutes', response_model=schemas.Traceroute)
def create_traceroute_for_target(id: int, traceroute: schemas.TracerouteCreate, db: Session = Depends(get_db)):
    return crud.create_target_traceroute(db=db, traceroute=traceroute, target_id=id)


@app.get('/target/{id}/traceroutes', response_model=schemas.Traceroute)
def read_traceroutes_for_target(id: int, skip: int = 0, limit: int = None, db: Session = Depends(get_db)):
    return crud.get_traceroutes_by_target(db=db, target_id=id, skip=skip, limit=limit)

@app.get('/traceroutes', response_model=List[schemas.Traceroute])
def read_traceroutes(skip: int = 0, limit: int = None, db: Session = Depends(get_db)):
    traceroutes = crud.get_traceroutes(db=db, skip=skip, limit=limit)
    print(traceroutes)
    return traceroutes


"""
GUI functions
"""

@app.get('/')
async def index(request: Request):
    if not config:
        return {'message': 'Config not loaded'}
    if not db_load_result:
        return {'message': 'Cannot access DB: {}'.format(db_load_result)}
    targets = traceroute_history_runner.list_targets(include_tr=True, formatting='web')
    return templates.TemplateResponse('targets.html',
                                      {'request': request, 'targets': targets, 'system': get_system_data()})


@app.get('/info')
async def info(request: Request):
    return {"message": "Hello", "root_path": request.scope.get("root_path")}


if __name__ == '__main__':
    # Run the web server
    uvicorn.run('user_interface:app', host=bind_to, port=bind_port, log_level='info', root_path=sub_directory, reload=True)


