#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

config_management handles all necessary connections to config files

"""

__intname__ = 'traceroute_history.config_management'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.4.1'
__build__ = '2020100701'

import os
import sys
from logging import getLogger
import re
import configparser
import exceptions

logger = getLogger(__name__)


def load_config(config_file):
    """
    Loads config from file

    :return: (ConfigParser) config object
    """
    global CONFIG

    if config_file is None or not os.path.isfile(config_file):
        raise exceptions.ConfigFileNotFound("Cannot load config file {}".format(config_file))
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
    except (configparser.MissingSectionHeaderError, KeyError):
        raise exceptions.ConfigFileNotParseable("Config file {} is not parseable.".format(config_file))
    return config


def save_config(config_file, config):
    """
    Saves config to file

    :return: (bool)
    """

    if config_file is None or not os.path.isfile(config_file):
        logger.error('Cannot save configuration file "{0}".'.format(config_file))

    try:
        with open(config_file, 'w') as fp:
            config.write(fp)
            return True
    except OSError as exc:
        logger.critical('Cannot save configuration file. {}'.format(exc))
        return False


def read_smokeping_config(config_file):
    """
    Read smokeping config file
    TODO: does not support missing title or target directives (will shift values)

    :param config_file: (str) path to config file
    :return: (list)(dict) [{'target': x, 'title': y}]
    """
    if config_file == '':
        return None
    if not os.path.isfile(config_file):
        logger.error('smokeping config "{0}" does not seem to be a file.'.format(config_file))
        return None

    target_regex = re.compile(r'^host\s*=\s*(\S*)$')
    title_regex = re.compile(r'^title\s*=\s*(.*)$')

    targets = []
    target_names = []

    with open(config_file, 'r') as smokeping_config:
        for line in smokeping_config:
            target = re.match(target_regex, line)
            target_name = re.match(title_regex, line)
            if target:
                targets.append(target)
            if target_name:
                target_names.append(target_name)

    if len(targets) != len(target_names):
        logger.error('Cannot parse smokeping config file. We need as much titles as host entries.')
        return None

    # TODO Add regex for group inclusion / exclusion

    return [{'target': target, 'name': name} for target, name in zip(targets, target_names)]


def get_targets_from_config(config):
    targets = [section.lstrip('TARGET:') for section in config.sections() if section.startswith('TARGET:')]
    try:
        smokeping_config = config['SMOKEPING_SOURCE']['smokeping_config_path']
    except KeyError:
        smokeping_config = None
    smokeping_targets = read_smokeping_config(smokeping_config)
    if smokeping_targets:
        targets = targets + smokeping_targets
    return targets


def get_groups_from_config(config, target_name):
    targets = get_targets_from_config(config)
    for target in targets:
        try:
            if target == target_name:
                return [group.strip() for group in config['TARGET:' + target]['groups'].split(',')]
        except KeyError:
            return None


def get_groups_for_target(target_name, regex):
    if re.match(target_name, regex):
        return get_groups_from_config(target_name)


def remove_target_from_config(config, name):
    try:
        config.remove_section('TARGET:' + name)
    except KeyError:
        pass
