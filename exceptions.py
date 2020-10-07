#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

exceptions defines all necessary error handling

"""

__intname__ = 'traceroute_history.exceptions'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.0'
__build__ = '2020100701'


class TRBaseException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ConfigFileNotFound(TRBaseException):
    pass


class ConfigFileNotParseable(TRBaseException):
    pass
