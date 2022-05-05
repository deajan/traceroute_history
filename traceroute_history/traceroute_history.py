#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

Targets are configured in a config file,
Also happens to read smokeping configuration files to populate targets to probe

"""

__intname__ = 'traceroute_history'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2022 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.5.0-dev'
__build__ = '2022050501'

import os
import sys
import getopt
import ofunctions
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep
from sqlalchemy import and_
import sqlalchemy.exc
from datetime import datetime, timedelta
from command_runner import command_runner
import json
from decimal import Decimal
from traceroute_history import config_management, trparse, schemas, models, crud
from pydantic import ValidationError
from traceroute_history.database import load_database, db_scoped_session

# colorama is not mandatory
try:
    import colorama
    if os.name == 'nt':
        colorama.init(convert=True)
except ImportError:
    pass

CONFIG_FILE = 'traceroute_history.conf'

LOG_FILE = os.path.join(os.path.dirname(__file__), os.path.splitext(os.path.basename(__file__))[0]) + '.log'
logger = ofunctions.logger_get_logger(log_file=LOG_FILE)


def format_string(string: str, formatting: str='console'):
    """
    Formats strings for console or web output


    :param string: (str) String to format (contains {% %} values)
    :param formatting: (str) console/web/none
    :return: (str) formatted string
    """
    if string is None or string is []:
        return string

    if formatting == 'web':
        green_color = '<span class="green traceroute-green" style="background-color: darkgreen; color:white">'
        red_color = '<span class="red traceroute-red" style="background-color: darkred; color:white">'
        end_color = '</span>'
    elif formatting == 'console':
        try:
            green_color = colorama.Back.LIGHTGREEN_EX + colorama.Fore.BLACK
            red_color = colorama.Back.LIGHTRED_EX + colorama.Fore.BLACK
        except NameError:
            # missing colorama module ?
            green_color = '\033[102m'
            red_color = '\033[101m'
        end_color = '\033[0m'
    else:
        green_color = red_color = end_color = ''

    string = string.replace('{% START_COLOR_GREEN %}', green_color)
    string = string.replace('{% START_COLOR_RED %}', red_color)
    string = string.replace('{% END_COLOR %}', end_color)

    if formatting == 'web':
        return string.replace('\n', '<br />')
    else:
        return string


def analyze_traceroutes(current_tr: str, previous_tr: str, rtt_detection_threshold: int=0):
    """
    Analyses two traceroutes for diffent hops, also checks for rtt increase
    Returns list of different hops and increased rtt times

    :param current_tr: (str) raw traceroute output
    :param previous_tr: (str) raw traceroute output
    :return: (list) list of different indexes, or where rtt difference is higher than detection threshold
    """
    try:
        current_tr_object = trparse.loads(current_tr)
    except trparse.InvalidHeader:
        logger.warning('Cannot parse current tr')
        return None, None

    try:
        previous_tr_object = trparse.loads(previous_tr)
    except trparse.InvalidHeader:
        logger.warning('Cannot parse previous tr')
        return None, None

    max_hops = max(len(current_tr_object.hops), len(previous_tr_object.hops))

    different_hops = []
    increased_rtt = []

    for index in range(max_hops):

        # Try to spot different hop hosts
        try:
            if not current_tr_object.hops[index].probes[0].ip == previous_tr_object.hops[index].probes[0].ip:
                different_hops.append(current_tr_object.hops[index].idx)
        except IndexError:
            try:
                different_hops.append(current_tr_object.hops[index].idx)
            except IndexError:
                different_hops.append(previous_tr_object.hops[index].idx)

        # Try to spot increased rtt
        if rtt_detection_threshold != 0:
            try:
                # Try to detect timeouts that did respond earlier
                if current_tr_object.hops[index].probes[0].rtt is None and isinstance(previous_tr_object.hops[index].probes[0].rtt,
                                                                               Decimal):
                    increased_rtt.append(current_tr_object.hops[index].idx)
                # Try to detect increses in rtt
                elif current_tr_object.hops[index].probes[0].rtt > (
                        previous_tr_object.hops[index].probes[0].rtt + rtt_detection_threshold):
                    increased_rtt.append(current_tr_object.hops[index].idx)
            except (IndexError, TypeError):
                pass

    return different_hops, increased_rtt


def traceroutes_difference_preformatted(tr1: models.Traceroute, tr2: models.Traceroute):
    """
    Outputs traceroute differences with color highlighting in console
    :param tr1: (Traceroute) Traceroute model object
    :param tr2: (Traceroute) Tracerouet model object
    :return: (str) diff colorred traceroute outputs
    """

    try:
        config = config_management.load_config(CONFIG_FILE)
        rtt_detection_threshold = int(config['TRACEROUTE_HISTORY']['rtt_detection_threshold'])
    except KeyError:
        rtt_detection_threshold = 0
    except TypeError:
        logger.warning('Bogus rtt_detection_threshold value.')
        rtt_detection_threshold = 0
    different_hops, increased_rtt = analyze_traceroutes(tr1.raw_traceroute, tr2.raw_traceroute, rtt_detection_threshold=rtt_detection_threshold)



    def _console_output(tr, color):
        console_output = ''
        for line in tr.split('\n'):
            # Check that line is a hop, also, hops
            try:
                # Since we count hop indexes from 0 in trparse, and hop output starts with 1
                index = int(line.split()[0])
            except (TypeError, IndexError, ValueError):
                console_output = '{0}{1}\n'.format(console_output, line)
                continue
            if index in different_hops or index in increased_rtt:
                console_output = '{0}{1}{2}{3}\n'.format(console_output, color, line, '{% END_COLOR %}')
            else:
                console_output = '{0}{1}\n'.format(console_output, line)
        return console_output

    try:
        return 'Traceroute recorded at {0}:\n{1}Traceroute recorded at {2}:\n{3}'.format(tr1.creation_date,
                                                                                     _console_output(tr1.raw_traceroute,
                                                                                                     '{% START_COLOR_GREEN %}'),
                                                                                     tr2.creation_date,
                                                                                     _console_output(tr2.raw_traceroute,
                                                                                                     '{% START_COLOR_RED %}'))
    except TypeError:
        return 'Cannot parse TR' # TODO

def os_traceroute(address):
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
        exit_code, output = command_runner(command, shell=True, encoding=encoding)
        if exit_code != 0:
            logger.error(
                'Traceroute to address: "{0}" failed with exit code {1}. Command output:'.format(address, exit_code))
            logger.error(output)
        return exit_code, output
    return 1, 'Bogus address given.'


def update_traceroute_database(target: schemas.TargetCreate):
    """
    Executes tracert for given name, and updates database accordingly

    :param target_name: (str) target user friendly name (can be anything)
    :param address: (str) hostname in fqdn, ipv4 or ipv6 format
    :param groups: (list)(str) list of groups to which this target belongs
    :return:
    """

    config = config_management.load_config(CONFIG_FILE)

    with db_scoped_session() as db:
        try:
            # Create groups if not exist
            tgt_groups = []
            for group in target.groups:
                grp = crud.get_group(db=db, name=group.name)
                if not grp:
                    grp = crud.create_group(db=db, group=group)
                    logger.info('Created new group "{0}".'.format(group.name))
                tgt_groups.append(grp)

            # Create targets if not exist
            tgt = crud.get_target(db=db, name=target.name)
            if not tgt:
                target.groups = tgt_groups
                target = crud.create_target(db=db, target=target)
                logger.info('Created new target "{0}".'.format(target.name))
            else:
                target = tgt

            # Get traceroute
            exit_code, raw_traceroute = os_traceroute(target.address)
            if exit_code == 0:
                previous_traceroute = crud.get_traceroutes_by_target(db=db, target_name=target.name, limit=1)
                if previous_traceroute:
                    try:
                        rtt_detection_threshold = int(config['TRACEROUTE_HISTORY']['rtt_detection_threshold'])
                    except KeyError:
                        rtt_detection_threshold = 0
                    except TypeError:
                        logger.warning('Bogus rtt_detection_threshold value.')
                        rtt_detection_threshold = 0
                    different_hops, increased_rtt = analyze_traceroutes(raw_traceroute, previous_traceroute[0].raw_traceroute, rtt_detection_threshold=rtt_detection_threshold)
                    # Special case where previous traceroute is failed (traceroute binary missing) or unparseable
                    if different_hops == None and increased_rtt == None:
                        current_traceroute = schemas.TracerouteCreate(raw_traceroute=raw_traceroute)
                        crud.create_target_traceroute(db=db, traceroute=current_traceroute, target_id=target.id)
                        logger.info('Created traceroute for target "{0}" since previous traceroute is unparseable.'.format(target.name))
                    elif different_hops or increased_rtt:
                        current_traceroute = schemas.TracerouteCreate(raw_traceroute=raw_traceroute)
                        crud.create_target_traceroute(db=db, traceroute=current_traceroute, target_id=target.id)
                        logger.info('Updating traceroute for target "{0}".'.format(target.name))
                    else:
                        logger.debug('Current traceroute is identical to previous one for target "{0}". Nothing to do.'.format(target.name))
                else:
                    current_traceroute = schemas.TracerouteCreate(raw_traceroute=raw_traceroute)
                    crud.create_target_traceroute(db=db, traceroute=current_traceroute, target_id=target.id)
                    logger.info('Created traceroute for target "{0}".'.format(target.name))
            else:
                logger.error('Cannot get traceroute for target "{0}".'.format(target.name))
                current_traceroute = schemas.TracerouteCreate(raw_traceroute=raw_traceroute)
                crud.create_target_traceroute(db=db, traceroute=current_traceroute, target_id=target.id)
        except sqlalchemy.exc.OperationalError as exc:
            logger.error('sqlalchemy operation error: {0}.'.format(exc))
            logger.error('Trace:', exc_info=True)


def get_last_traceroutes(target_name, limit=1):
    """
    Lists traceroute executions for a given target

    :param name: (str) target name
    :param limit: (int) number of executions to fetch, if None, all are fetched
    :return: (list)(Traceroutes) list of traceroute object

    """

    with db_scoped_session() as db:
        traceroutes = crud.get_traceroutes_by_target(db=db, target_name=target_name, limit=limit)
        return traceroutes


def get_last_traceroutes_formatted(name, limit=1, formatting='console'):
    traceroutes = get_last_traceroutes(name, limit=limit)
    if traceroutes is False:
        logger.warning('Target "{0}" has been requested but does not exist in database.'.format(name))
        return 'Target not found in database.'
    if traceroutes:
        output = 'Target has {0} tracreoute entries.'.format(len(traceroutes))
        length = len(traceroutes)
        if len(traceroutes) > 1:
            output = output + traceroutes_difference_preformatted(traceroutes[0], traceroutes[1])
            for i in range(length - 2):
                output = output + traceroutes[i + 2].__repr__()
        else:
            for traceroute in traceroutes:
                output = output + traceroute.__repr__()
    else:
        output = traceroutes

    return format_string(output, formatting)


def list_targets(include_tr: bool=False, formatting: str='console'):

    with db_scoped_session() as db:
        output = []

        targets = crud.get_targets(db=db)
        for target in targets:
            groups = crud.get_groups_by_target(db=db, target_id=target.id)
            traces = get_last_traceroutes(target.name, limit=2)
            try:
                current_tr = traces[0]
                current_tr_object = trparse.loads(current_tr.raw_traceroute)
                current_rtt = float(current_tr_object.global_rtt)
            # TypeError may happen if the traceroute could not be done, hence global.rtt does not contain an int type str
            except (trparse.ParseError, TypeError):
                current_rtt = None
            try:
                previous_tr = traces[1]
                previous_tr_object = trparse.loads(previous_tr.raw_traceroute)
                previous_rtt = float(previous_tr_object.global_rtt)
            except (IndexError, trparse.ParseError, TypeError):
                previous_tr = None
                previous_rtt = None

            target = {'id': target.id, 'name': target.name, 'address': target.address, 'groups': [group.name for group in groups],
                           'current_rtt': current_rtt, 'previous_rtt': previous_rtt,
                           'last_probe': current_tr.creation_date }
            if include_tr:
                if previous_tr:
                    target['current_tr'] = format_string(traceroutes_difference_preformatted(current_tr, previous_tr), formatting)
                else:
                    target['current_tr'] = format_string(current_tr.raw_traceroute, formatting)


            output.append(target)
        return output


def delete_old_traceroutes(target_name: str, days: int, keep: int):
    """
    Deletes old traceroute data if days have passed, but always keep at least limit entries

    :param target_name: (str) target name
    :param days: (int) number of days after which a traceroute will be deleted
    :param keep: (int) number of traceroutes to keep regardless of the
    :return:
    """

    with db_scoped_session() as db:
        target = crud.get_target(db=db, name=target_name)
        if not target:
            return None

        num_records = crud.get_traceroutes_by_target(db=db, target_name=target_name, count=True)
        if num_records > keep:
            num_records_to_delete = num_records - keep

            # TODO: IS NOT CRUD CONVERTED

            # Subquery is needed because we cannot use delete() on a query with a limit
            subquery = db.query(models.Traceroute.id).filter(and_(models.Traceroute.target == target,
                                                                  models.Traceroute.creation_date < (datetime.now() - timedelta(
                                                                    days=days)))).order_by(models.Traceroute.id.desc()).limit(
                num_records_to_delete).subquery()
            records = db.query(models.Traceroute).filter(models.Traceroute.id.in_(subquery)).delete(synchronize_session='fetch')
            logger.info('Deleted {0} old records for target "{1}".'.format(records, target_name))



def remove_target(target_name):
    config = config_management.load_config(CONFIG_FILE)
    config_management.remove_target_from_config(config, target_name)
    delete_old_traceroutes(target_name, 0, 0)
    return config_management.save_config(CONFIG_FILE, config)


def execute(daemon=False):
    """
    Execute traceroute updates and housekeeping for all targets

    :param daemon: (bool) Should this run in a loop
    :return:
    """
    config = config_management.load_config(CONFIG_FILE)
    target_names = config_management.get_targets_from_config(config)

    if len(target_names) == 0:
        logger.info('No valid targets given.')
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

    for target_name in target_names:
        try:
            grp = [schemas.GroupCreate(name=grp_name) for grp_name in config_management.get_groups_from_config(config, target_name)]
            tgt = schemas.TargetCreate(name=str(target_name), address=config['TARGET:' + target_name]['address'], groups=grp)

            job_kwargs = {
                'target': tgt
            }

            delete_kwargs = {
                'target_name': target_name,
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

            # TODO add regular config file reloading job ?

        except KeyError as exc:
            logger.error('Failed to read configuration for target "{0}": {1}.'.format(target_name, exc))
        except ValidationError as exc:
            logger.error('Bogus target "{0}" given: {1}.'.format(target_name, exc))

    run_once = True
    try:
        while daemon or run_once:
            run_once = False
            sleep(1)
    except KeyboardInterrupt:
        logger.info('Interrupted by keyboard')
        scheduler.shutdown()


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
    print('--daemon                             Run as daemon')
    print('--update-now                         Manual update of traceroute targets')
    print(
        '--get-traceroutes-for=name[,x]       Print x traceroutes for target "name". If no x value is given, all are shown')
    print('--remove-target=name                 Removes given target from configuration and deletes target data from database')
    print('--list-targets                       Extract a list of current targets in database"')
    print('--init-db                            Initialize a fresh database.')
    sys.exit()


def main(argv):
    global CONFIG_FILE
    global logger

    try:
        opts, _ = getopt.getopt(argv, "h?",
                                ['config=', 'get-traceroutes-for=', 'list-targets',
                                 'remove-target=',
                                 'daemon', 'update-now',
                                 'init-db', 'help'])
    except getopt.GetoptError:
        help_()
        sys.exit(9)

    config_file_set = False
    for opt, arg in opts:
        if opt == '--config':
            CONFIG_FILE = arg
            config_file_set = True

    # Reload config before executing anything elsee
    config = config_management.load_config(CONFIG_FILE)
    try:
        log_file = config['TRACEROUTE_HISTORY']['log_file']
        logger = ofunctions.logger_get_logger(log_file=log_file)
    except KeyError:
        pass

    if not config_file_set:
        logger.info('No config file set. trying default one: {0}.'.format(os.path.abspath(CONFIG_FILE)))

    if os.name != 'nt':
        if os.getuid() != 0:
            logger.warn('This program should probably be run as root so traceroute can work.')

    initialize = False
    for opt, arg in opts:
        if opt == '--init-db':
            initialize = True

    load_database(config, initialize=initialize)

    opt_found = False
    for opt, arg in opts:
        if opt == '--get-traceroutes-for':
            try:
                target, limit = arg.split(',')
                limit = int(limit)
            except (ValueError, TypeError):
                target = arg
                limit = None
            print(get_last_traceroutes_formatted(target, limit))
            sys.exit(0)
        if opt == '--list-targets':
            print('List of current targets in database (not necessary in the config file:')
            print(json.dumps(list_targets(), indent=2, sort_keys=True, default=str))
            sys.exit(0)
        if opt == '--remove-target':
            res = remove_target(arg)
            sys.exit(res)
        if opt == '--daemon':
            opt_found = True
            execute(daemon=True)
        if opt == '--update-now':
            opt_found = True
            execute()
        if opt == '--help' or opt == 'h' or opt == '?':
            opt_found = True
            help_()
    if not opt_found:
        help_()


if __name__ == '__main__':
    main(sys.argv[1:])
