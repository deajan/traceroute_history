#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Database handling

"""

__intname__ = 'traceroute_history.database'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.4.0'
__build__ = '2020050601'

import os
import sys
from logging import getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sqlalchemy.exc
from contextlib import contextmanager
import urllib.parse
from traceroute_history import models

logger = getLogger(__name__)


SessionLocal = None

# Dependency for FastAPI
def get_db():
    if SessionLocal is None:
        raise TypeError('SessionLocal DB not initialized')
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# For internal DB requests
@contextmanager
def db_scoped_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
        session.flush()
    except:
        session.rollback()
        raise
    finally:
        pass #TODO
        #session.close()

def load_database(config, initialize=False):
    """
    Initiates database session as scoped session so we can reutilise the factory in a threaded model

    :return:
    """

    global SessionLocal

    db_driver = config['TRACEROUTE_HISTORY']['database_driver']
    db_host = config['TRACEROUTE_HISTORY']['database_host']

    try:
        db_user = urllib.parse.quote_plus(config['TRACEROUTE_HISTORY']['database_user'])
        db_password = urllib.parse.quote_plus(config['TRACEROUTE_HISTORY']['database_password'])
    except KeyError:
        db_user = None
        db_password = None
    try:
        db_name = config['TRACEROUTE_HISTORY']['database_name']
    except KeyError:
        db_name = None

    if db_driver == 'sqlite' and not os.path.isfile(db_host) and initialize is False:
        logger.critical('No database file: "{0}". Please provide path in configuration file, or use --init-db to create a new database.'.format(db_host))
        sys.exit(3)

    if db_driver == 'sqlite':
        db_name = ''
    elif db_name:
        db_name = '/' + db_name

    if db_user and db_password and db_driver != 'sqlite':
        connection_string = '{0}:///{1}:{2}@{3}{4}'.format(db_driver, db_user, db_password, db_host, db_name)
    else:
        connection_string = '{0}:///{1}{2}'.format(db_driver, db_host, db_name)

    logger.debug('SQL Connection string "{0}".'.format(connection_string))
    if initialize:
        db_engine = create_engine(connection_string, echo=True)
        models.init_db(db_engine)
        logger.info('DB engine initialization finished.')
        sys.exit(0)
    else:
        try:
            logger.debug('Trying to open {0} database "{1}{2}" as user "{2}".'.format(db_driver, db_host, db_name, db_user, db_password))

            # FastAPI will use more than one thread to interact with the database for a single request
            # We need to disable thread check
            # Warning: Check that we always use different threads when using scheduler
            engine = create_engine(connection_string, connect_args={'check_same_thread': False})
            session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            SessionLocal =  scoped_session(session_factory)
            return SessionLocal
        except sqlalchemy.exc.OperationalError:
            logger.critical('Cannot connect to database "{0}".'.format(db_host), exc_info=True)
            return None
