#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
command_runner is a quick tool to launch commands from Python, get exit code
and output, and handle most errors that may happen

Versionning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionnality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'command_runner'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.4.1'
__build__ = '2020040201'


import os
from logging import getLogger
import subprocess


logger = getLogger()


def command_runner(command, valid_exit_codes=None, timeout=300, shell=False, encoding='utf-8',
                   windows_no_window=False, **kwargs):
    """
    Whenever we can, we need to avoid shell=True in order to preseve better security
    Runs system command, returns exit code and stdout/stderr output, and logs output on error
    valid_exit_codes is a list of codes that don't trigger an error
    
    Accepts subprocess.check_output arguments
        
    """

    # Set default values for kwargs
    errors = kwargs.pop('errors', 'backslashreplace')  # Don't let encoding issues make you mad
    universal_newlines = kwargs.pop('universal_newlines', False)
    creationflags = kwargs.pop('creationflags', 0)
    if windows_no_window:
        creationflags = creationflags | subprocess.CREATE_NO_WINDOW

    try:
        # universal_newlines=True makes netstat command fail under windows
        # timeout does not work under Python 2.7 with subprocess32 < 3.5
        # decoder may be unicode_escape for dos commands or utf-8 for powershell
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=shell,
                                         timeout=timeout, universal_newlines=universal_newlines, encoding=encoding,
                                         errors=errors, creationflags=creationflags, **kwargs)

    except subprocess.CalledProcessError as exc:
        exit_code = exc.returncode
        try:
            output = exc.output
        except Exception:
            output = "command_runner: Could not obtain output from command."
        if exit_code in valid_exit_codes if valid_exit_codes is not None else [0]:
            logger.debug('Command [%s] returned with exit code [%s]. Command output was:' % (command, exit_code))
            if isinstance(output, str):
                logger.debug(output)
            return exc.returncode, output
        else:
            logger.error('Command [%s] failed with exit code [%s]. Command output was:' %
                         (command, exc.returncode))
            logger.error(output)
            return exc.returncode, output
    # OSError if not a valid executable
    except (OSError, IOError) as exc:
        logger.error('Command [%s] failed because of OS [%s].' % (command, exc))
        return None, exc
    except subprocess.TimeoutExpired:
        logger.error('Timeout [%s seconds] expired for command [%s] execution.' % (timeout, command))
        return None, 'Timeout of %s seconds expired.' % timeout
    except Exception as exc:
        logger.error('Command [%s] failed for unknown reasons [%s].' % (command, exc))
        logger.debug('Error:', exc_info=True)
        return None, exc
    else:
        logger.debug('Command [%s] returned with exit code [0]. Command output was:' % command)
        if output:
            logger.debug(output)
        return 0, output


def deferred_command(command, defer_time=None):
    """
    This is basically an ugly hack to launch commands in windows which are detached from parent process
    Especially useful to auto update/delete a running executable

    """
    if not isinstance(defer_time, int):
        raise ValueError('defer_time needs to be in seconds.')
        
    if os.name == 'nt':
        deferrer = 'ping 127.0.0.1 -n %s > NUL & ' % defer_time
    else:
        deferrer = 'ping 127.0.0.1 -c %s > /dev/null && ' % defer_time
        
    subprocess.Popen(deferrer + command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
    

def _selftest():
    print('Example code for %s, %s, %s' % (__intname__, __version__, __build__))
    exit_code, output = command_runner('ping 127.0.0.1')
    assert exit_code == 0, 'Exit code should be 0 for ping command'
    
    exit_code, output = command_runner('ping 127.0.0.1', timeout=1)
    assert exit_code == None, 'Exit code should be none on timeout'   
    assert 'Timeout' in output, 'Output should have timeout'


if __name__ == '__main__':
    _selftest()
