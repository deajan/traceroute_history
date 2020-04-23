#! /usr/bin/env python
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Hosts can be configured in a config file,
Also happens to read smokeping configuration files to populate hosts to probe

"""

__intname__ = 'traceroute_history'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.0'
__build__ = '2020042201'

# TODO: Use scappy as alternative internal traceroute implementation

import os
import sys
import re
import getopt
import ofunctions
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, scoped_session
import sqlalchemy.exc
from datetime import datetime, timedelta
from command_runner import command_runner
import trparse
from sql_declaration import Target, Traceroute, Group, init_db
import configparser
from contextlib import contextmanager

# colorama is not mandatory
try:
    import colorama

    if os.name == 'nt':
        colorama.init(convert=True)
except ImportError:
    pass

CONFIG_FILE = 'traceroute_history.conf'
SMOKEPING_CONFIG_FILE = None
DB_SESSION = None
CONFIG = None

LOG_FILE = os.path.join(os.path.dirname(__file__), os.path.splitext(os.path.basename(__file__))[0]) + '.log'
logger = ofunctions.logger_get_logger(log_file=LOG_FILE)


def diff_traceroutes(tr1: str, tr2: str):
    """
    Checks whether two traceroute outputs are different, and returns list of different hops

    :param tr1: (str) raw traceeroute output
    :param tr2: (str) raw
    :return: (list)
    """
    tr1_object = trparse.loads(tr1)
    tr2_object = trparse.loads(tr2)

    max_hops = max(len(tr1_object.hops), len(tr2_object.hops))

    different_hops = []

    # Traceroute indexes begin with 1 instead of 0
    for index in range(max_hops):
        try:
            if not tr1_object.hops[index].probes[0].ip == tr2_object.hops[index].probes[0].ip:
                different_hops.append(index)
        except IndexError:
            different_hops.append(index)

    return different_hops


def traceroutes_difference_console(tr1, tr2):
    """
    Outputs traceroute differences with color highlighting in console
    :param tr1: (str) Traceroute sqlalchemy object
    :param tr2: (str) Tracerouet sqlalchemy object
    :return: (str) diff colorred traceroute outputs
    """
    different_hops = diff_traceroutes(tr1.traceroute, tr2.traceroute)

    def _console_output(tr, color):
        console_output = ''
        for line in tr.split('\n'):
            # Check that line is a hop, also, hops
            try:
                # Since we count hop indexes from 0 in trparse, and hop output starts with 1
                index = int(line.split()[0]) - 1
            except (TypeError, IndexError, ValueError):
                console_output = '{0}{1}\n'.format(console_output, line)
                continue
            if index in different_hops:
                console_output = '{0}{1}{2}{3}\n'.format(console_output, color, line, '\033[0m')
            else:
                console_output = '{0}{1}\n'.format(console_output, line)
        return console_output

    try:
        return 'Traceroute recorded at {0}:\n{1}Traceroute recorded at {2}:\n{3}'.format(tr1.creation_date,
                                                                                         _console_output(tr1.traceroute,
                                                                                                         colorama.Back.LIGHTGREEN_EX + colorama.Fore.BLACK),
                                                                                         tr2.creation_date,
                                                                                         _console_output(tr2.traceroute,
                                                                                                         colorama.Back.LIGHTRED_EX + colorama.Fore.BLACK))
    # NameError happens if colorama isn't loaded
    except NameError:
        return 'Traceroute recorded at {0}:\n{1}Traceroute recorded at {2}:\n{3}'.format(tr1.creation_date,
                                                                                         _console_output(tr1.traceroute,
                                                                                                         '\033[102m'),
                                                                                         tr2.creation_date,
                                                                                         _console_output(tr2.traceroute,
                                                                                                         '\033[101m'))


def get_traceroute(address):
    """
    Launches actuel traceroute binary

    :param address: (str) address
    :return: (str) raw traceroute output
    """
    if address:
        if os.name == 'nt':
            executable = 'tracert'
            # Ugly hack se we get actual characters encoding right from cmd.exe
            # Also encodes "well" cp850 using cp437 parameter
            encoding = 'cp437'
        else:
            executable = 'traceroute'
            encoding = 'utf-8'
        command = '{0} {1}'.format(executable, address)
        exit_code, output = command_runner(command, shell=False, encoding=encoding)
        if exit_code == 0:
            return output
        else:
            logger.error(output)
    return None


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = DB_SESSION()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        pass
        # session.close()


def insert_traceroute(target, traceroute_output):
    """
    Creates new traceroute entry in DB

    :param target: Target SQL object
    :param traceroute_output: raw traceroute output
    :return:
    """
    traceroute = Traceroute(traceroute=traceroute_output, target=target)
    with session_scope() as session:
        session.add(traceroute)


def create_group(name, target):
    pass


def create_target(name, address=None, groups=None):
    """
    Creates new target (host) to monitor in DB

    :param name: (str) host user friendly name (can be anything)
    :param address: (str) hostname in fqdn, ipv4 or ipv6 format
    :param groups: (list)(str) list of groups to which this target belongs
    :return: (Target) target object
    """
    # for group in groups:
    #    try:
    #        group = db_session.query(Group).filter(Group.name == group).one()

    target = Target(name=name, address=address)
    with session_scope() as session:
        session.add(target)

    return target


def update_traceroute_database(name, address, groups):
    """
    Executes tracert for given name, and updates database accordingly

    :param name: (str) host user friendly name (can be anything)
    :param address: (str) hostname in fqdn, ipv4 or ipv6 format
    :param groups: (list)(str) list of groups to which this target belongs
    :return:
    """

    try:
        with session_scope() as session:
            try:
                target = session.query(Target).filter(Target.name == name).one()
            except sqlalchemy.orm.exc.NoResultFound:
                target = None
            if not target:
                # miss ipv4 and others
                target = create_target(name, address, groups)
                logger.info('Created new target: {0}.'.format(name))
            current_trace = get_traceroute(target.address)
            if current_trace:
                last_trace = session.query(Traceroute).filter(Traceroute.target == target).order_by(
                    Traceroute.id.desc()).first()
                if last_trace:
                    if diff_traceroutes(last_trace.traceroute, current_trace):
                        insert_traceroute(target, current_trace)
                        logger.info('Updating different traceroute for target: {0}.'.format(name))
                    else:
                        logger.debug('Traceroute identical to last one for target: {0}. Nothing to do.'.format(name))
                else:
                    insert_traceroute(target, current_trace)
                    logger.info('Created first tracreoute entry for target: {0}.'.format(name))
            else:
                logger.error('Cannot get traceroute for target: {0}.'.format(name))
    except sqlalchemy.exc.OperationalError as exc:
        logger.error('sqlalchemy operation error: {0}.'.format(exc))
        logger.error('Trace:', exc_info=True)


def get_last_traceroutes(name, limit=1):
    """
    Lists traceroute executions for a given target

    :param name: (str) target name
    :param limit: (int) number of executions to fetch, if None, all are fetched
    :return: (list)(Traceroutes) list of traceroute object

    """
    with session_scope() as session:
        try:
            target = session.query(Target).filter(Target.name == name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None

        last_trace = session.query(Traceroute).filter(Traceroute.target == target).order_by(Traceroute.id.desc()).limit(
            limit).all()
        return last_trace


def delete_old_traceroutes(name: str, days: int, keep: int):
    """
    Deletes old traceroute data if days have passed, but always keep at least limit entries

    :param name: (str) target name
    :param days: (int) number of days after which a traceroute will be deleted
    :param keep: (int) number of traceroutes to keep regardless of the
    :return:
    """

    with session_scope() as session:
        try:
            target = session.query(Target).filter(Target.name == name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None

        num_records = session.query(Traceroute).filter(Traceroute.target == target).count()
        if num_records > keep:
            num_records_to_delete = num_records - keep
            # Subquery is needed because we cannot use delete() on a query with a limit
            subquery = session.query(Traceroute.id).filter(and_(Traceroute.target == target,
                                                                Traceroute.creation_date < (datetime.now() - timedelta(
                                                                    days=days)))).order_by(Traceroute.id.desc()).limit(
                num_records_to_delete).subquery()
            records = session.query(Traceroute).filter(Traceroute.id.in_(subquery)).delete(synchronize_session='fetch')
            logger.info('Deleted {0} old records for target: {1}.'.format(records, name))


def read_smokeping_config(config_file):
    """
    Read smokeping config file
    TODO: does not support missing title or host directives (will shift values)

    :param config_file: (str) path to config file
    :return: (list)(dict) [{'host': x, 'title': y}]
    """
    if config_file == '':
        return None
    if not os.path.isfile(config_file):
        logger.error('smokeping config "{0}" does not seem to be a file.'.format(config_file))
        return None

    host_regex = re.compile(r'^host\s*=\s*(\S*)$')
    title_regex = re.compile(r'^title\s*=\s*(.*)$')

    hosts = []
    names = []

    with open(config_file, 'r') as smokeping_config:
        for line in smokeping_config:
            host = re.match(host_regex, line)
            name = re.match(title_regex, line)
            if host:
                hosts.append(host)
            if name:
                names.append(host)

    if len(hosts) != len(names):
        logger.error('Cannot parse smokeping config file. We need as much titles as host entries.')
        return None

    # TODO Add regex for group inclusion / exclusion

    return [{'host': host, 'name': name} for host, name in zip(hosts, names)]


def execute(daemon=False):
    """
    Execute traceroute updates and housekeeping for all hosts

    :param daemon: (bool) Should this run in a loop
    :return:
    """
    config = CONFIG
    hosts = [section for section in config.sections() if section.startswith('HOST_')]
    try:
        smokeping_config = config['SMOKEPING_SOURCE']['smokeping_config_path']
    except KeyError:
        smokeping_config = None
    smokeping_hosts = read_smokeping_config(smokeping_config)
    if smokeping_hosts:
        hosts = hosts + smokeping_hosts

    if len(hosts) == 0:
        logger.info('No valid hosts given.')
        sys.exit(20)

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Interval between traceroute executions
    try:
        interval = int(config['TRACEROUTE_HISTORY']['interval'])
    except KeyError:
        interval = 3600
    except TypeError:
        logger.error('Bogus interval value. Using default value.')
        interval = 3600

    try:
        delete_history_days = int(config['TRACEROUTE_HISTORY']['delete_history_days'])
    except KeyError:
        delete_history_days = None
    except TypeError:
        logger.error('Bogus delete_history_days value. Deactivating cleanup.')
        delete_history_days = None
    try:
        minimum_keep = int(config['TRACEROUTE_HISTORY']['minimum_keep'])
    except KeyError:
        minimum_keep = 100
    except TypeError:
        logger.error('Bogus minimum_keep value. Using default.')
        minimum_keep = 100

    for host in hosts:
        try:
            target_name = config[host]['name']
            job_kwargs = {
                'name': config[host]['name'],
                'address': config[host]['address'],
                'groups': config[host]['groups']
            }
            delete_kwargs = {
                'name': config[host]['name'],
                'days': delete_history_days,
                'keep': minimum_keep
            }

            # Immediate start
            scheduler.add_job(update_traceroute_database, None, [], job_kwargs, name='startup-' + target_name,
                              id='startup-' + target_name)
            # Programmed start afterwards
            scheduler.add_job(update_traceroute_database, 'interval', [], job_kwargs, seconds=interval,
                              name=target_name, id=target_name)

            if delete_history_days:
                scheduler.add_job(delete_old_traceroutes, None, [], delete_kwargs,
                                  name='startup-housekeeping-' + target_name, id='startup-housekeeping-' + target_name)
                scheduler.add_job(delete_old_traceroutes, 'interval', [], delete_kwargs, hours=1,
                                  name='housekeeping-' + target_name, id='housekeeping-' + target_name)
        except KeyError as exc:
            logger.error('Failed to read configuration for host: {0}: {1}.'.format(host, exc))

    run_once = True
    try:
        while daemon or run_once:
            run_once = False
            sleep(1)
    except KeyboardInterrupt:
        logger.info('Interrupted by keyboard')
        scheduler.shutdown()


def load_config():
    """
    Loads config from file

    :return: (ConfigParser) config object
    """
    if CONFIG_FILE is None or not os.path.isfile(CONFIG_FILE):
        print(
            'Cannot load configuration file: {0}. Please use --config=[config file].'.format(CONFIG_FILE))
        sys.exit(10)
    config = configparser.ConfigParser()
    try:
        config.read(CONFIG_FILE)
        if config['TRACEROUTE_HISTORY']['database_driver'] != 'sqlite3' and not os.path.isfile(
                config['TRACEROUTE_HISTORY']['database_host']):
            print('No valid sqlite configuration found.')
            sys.exit(11)
    except (configparser.MissingSectionHeaderError, KeyError):
        print('Unknown database configuration.')
        sys.exit(12)
    return config


def load_database(host):
    """
    Initiates database session as scoped session so we can reutilise the factory in a threaded model

    :return:
    """
    global DB_SESSION
    if not os.path.isfile(host):
        raise FileNotFoundError('No database file: {0}'.format(host))
    engine = create_engine('sqlite:///{0}'.format(host), echo=False)
    session_factory = sessionmaker(bind=engine)
    DB_SESSION = scoped_session(session_factory)


def help_():
    print('{} {} {}'.format(__intname__, __version__, __build__))
    print('{} under {}'.format(__copyright__, __licence__))
    print('')
    print('Usage:')
    print('{} [options]')
    print('')
    print('Options:')
    print('')
    print(
        '--config=                            Path to config file. If none given, traceroute_history.conf in the current directory is tried.')
    print(
        '--smokeping-config=                  Optional path to smokeping config, in order to read additional targets from')
    print('--daemon                             Run as daemon')
    print('--update-now                         Manual update of traceroute targets')
    print(
        '--get-traceroutes-for=host[,x]       Print x traceroutes for target "host". If no x value is given, all are shown')
    print('--init-db                            Initialize a fresh database.')
    sys.exit()


def main(argv):
    global CONFIG
    global CONFIG_FILE
    global SMOKEPING_CONFIG_FILE
    global logger

    try:
        opts, _ = getopt.getopt(argv, "h?",
                                ['config=', 'smokeping-config=', 'get-traceroutes-for=', 'daemon', 'update-now',
                                 'init-db', 'help'])
    except getopt.GetoptError:
        help_()
        sys.exit(9)

    for opt, arg in opts:
        if opt == '--config':
            CONFIG_FILE = arg
        if opt == '--smokeping-config':
            SMOKEPING_CONFIG_FILE = arg

    # Reload config before executing anything elsee
    CONFIG = load_config()
    try:
        log_file = CONFIG['TRACEROUTE_HISTORY']['log_file']
        logger = ofunctions.logger_get_logger(log_file=log_file)
    except KeyError:
        pass

    if os.name != 'nt':
        if os.getuid() != 0:
            logger.warn('This program should probably be run as root so traceroute can work.')

    for opt, arg in opts:
        if opt == '--init-db':
            db_engine = create_engine('sqlite:///{0}'.format(CONFIG['TRACEROUTE_HISTORY']['database_host']), echo=True)
            init_db(db_engine)

    load_database(CONFIG['TRACEROUTE_HISTORY']['database_host'])

    for opt, arg in opts:
        if opt == '--get-traceroutes-for':
            try:
                host, limit = arg.split(',')
                limit = int(limit)
            except (ValueError, TypeError):
                host = arg
                limit = None
            traceroutes = get_last_traceroutes(host, limit=limit)
            if traceroutes:
                if len(traceroutes) > 1:
                    print(traceroutes_difference_console(traceroutes[0], traceroutes[1]))
                    for i in range(2):
                        traceroutes.pop()
                for traceroute in traceroutes:
                    print(traceroute)
            else:
                print(traceroutes)
            sys.exit()
        if opt == '--daemon':
            execute(daemon=True)
        if opt == '--update-now':
            execute()
        if opt == '--help' or opt == 'h' or opt == '?':
            help_()


if __name__ == '__main__':
    main(sys.argv[1:])
