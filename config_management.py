#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

config_management handles all necessary connections to config files

"""

__intname__ = 'traceroute_history.config_management'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2022 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.5.0-dev'
__build__ = '2022050501'

import os
from logging import getLogger
import re
import configparser
import exceptions

logger = getLogger(__name__)

# Don't add $ since we could have some comments afterwards
COMMENT_REGEX = re.compile(r"\s*#")
SMOKEPING_TARGET_REGEX = re.compile(r'.*host\s*=\s*(\S*)', re.IGNORECASE)
SMOKEPING_TITLE_REGEX = re.compile(r'.*title\s*=\s*(.*)$', re.IGNORECASE)


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

def read_include_file(include_file):
    """
    Read smokeping include files
    """

    targets = []
    target_names = []

    with open(include_file, 'r', encoding="utf-8") as smokeping_include_config:
        for line in smokeping_include_config:
            target = re.match(SMOKEPING_TARGET_REGEX, line)
            target_name = re.match(SMOKEPING_TITLE_REGEX, line)
            if target:
                targets.append(target)
            if target_name:
                target_names.append(target_name)
    return targets, target_names

def read_smokeping_config(config_file):
    """
    Read smokeping config file

    :param config_file: (str) path to config file
    :return: (list)(dict) [{'target': x, 'title': y}]
    """

    if config_file == '':
        return None
    if not os.path.isfile(config_file):
        logger.error('smokeping config "{0}" does not seem to be a file.'.format(config_file))
        return None

    targets = {}
    target_names = {}

    targets_section = False
    host_counter = 0

    with open(config_file, 'r') as smokeping_config:
        for line in smokeping_config:
            # Remove EOL
            line = line.rstrip()

            # Walk file until we hit targets section
            if line == "*** Targets ***":
                targets_section = True
                continue
            if not targets_section:
                continue
            # Stop reading file after another section is reached
            if line.startswith("*** "):
                targets_section = False
                continue

            if line.startswith("@include"):
                _, include_path = line.split("@include ")

                # Try to resolve abs filename, if not, try local
                if not os.path.isfile(include_path):
                    include_path = os.path.join(os.path.dirname(config_file), os.path.basename(include_path))

                with open(include_path, 'r') as include_file:
                    iterator = include_file.readlines()
            else:
                iterator = [line]

            for ln in iterator:
                # Remove EOL (again, but may be from include file this time)
                ln = ln.rstrip()

                # Let's begin searching for hosts, we'll get
                if ln.startswith("+"):
                    host_counter += 1

                if re.match(COMMENT_REGEX, ln):
                    continue
                target = re.match(SMOKEPING_TARGET_REGEX, ln)
                target_name = re.match(SMOKEPING_TITLE_REGEX, ln)

                if target:
                    targets[host_counter] = target.group(1)
                if target_name:
                    target_names[host_counter] = target_name.group(1)


    # TODO Add regex for group inclusion / exclusion

    # Merge targets and names into list when target host exists
    target_list = []
    for count in range(1, host_counter + 1):
        try:
            tgt = {'target': targets[count]}
        except KeyError:
            continue
        try:
            tgt['name'] = target_names[count]
        except KeyError:
            pass
        target_list.append(tgt)

    return target_list


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
