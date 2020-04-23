#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of ofunctions module

"""
ofunctions is a general library for basic repetitive tasks that should be no brainers :)

Versionning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionnality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'ofunctions'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2014-2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.5.0'
__build__ = '2020040201'


import os
import sys
import re
import logging
import tempfile
import time
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__name__)

# Logging functions ########################################################

FORMATTER = logging.Formatter(u'%(asctime)s :: %(levelname)s :: %(message)s')
MP_FORMATTER = logging.Formatter(u'%(asctime)s :: %(levelname)s :: %(processName)s :: %(message)s')


# Allows to change default logging output or record events
class ContextFilterWorstLevel(logging.Filter):
    def __init__(self):
        self.worst_level = logging.INFO
        super().__init__()

    def filter(self, record):
        # Examples
        # record.msg = f'{record.msg}'.encode('ascii', errors='backslashreplace')
        # When using this filter, ysomething can be added to logging.Formatter like '%(something)s'
        # record.something = 'value'
        if record.levelno > self.worst_level:
            self.worst_level = record.levelno
        return True


def logger_get_console_handler(multiprocessing_formatter=False):
    if multiprocessing_formatter:
        formatter = MP_FORMATTER
    else:
        formatter = FORMATTER

    # When Nuitka compiled under Windows, calls to subshells are opened as cp850 / other system locale
    # This behavior makes logging popen output to stdout/stderr fail
    # Let's force stdout and stderr to always be utf-8
    if os.name == 'nt':
        # https: // stackoverflow.com / a / 52372390 / 2635443
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
            sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
            # Alternative
            # import codecs
            # sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
        except AttributeError:
            print('Cannot force console encoding.')
            # IPython interpreter does not know about sys.stdout.reconfigure function
            # Neither does it now detach or fileno()
            #sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='backslashreplace', buffering=1)
            #sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='backslashreplace', buffering=1)

    try:
        console_handler = logging.StreamHandler(sys.stdout)
    except OSError as exc:
        print('Cannot log to stdout, trying stderr. Message %s' % exc)
        try:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            return console_handler
        except OSError as exc:
            print('Cannot log to stderr neither. Message %s' % exc)
            return False
    else:
        console_handler.setFormatter(formatter)
        return console_handler


def logger_get_file_handler(log_file, multiprocessing_formatter=False):
    if multiprocessing_formatter:
        formatter = MP_FORMATTER
    else:
        formatter = FORMATTER
    err_output = None
    try:
        file_handler = RotatingFileHandler(log_file, mode='a', encoding='utf-8', maxBytes=1024000, backupCount=3)
    except OSError as exc:
        try:
            print('Cannot create logfile. Trying to obtain temporary log file.\nMessage: %s' % exc)
            err_output = str(exc)
            temp_log_file = tempfile.gettempdir() + os.sep + __name__ + '.log'
            print('Trying temporary log file in ' + temp_log_file)
            file_handler = RotatingFileHandler(temp_log_file, mode='a', encoding='utf-8', maxBytes=1000000,
                                               backupCount=1)
            file_handler.setFormatter(formatter)
            err_output += '\nUsing [%s]' % temp_log_file
            return file_handler, err_output
        except OSError as exc:
            print('Cannot create temporary log file either. Will not log to file. Message: %s' % exc)
            return False
    else:
        file_handler.setFormatter(formatter)
        return file_handler, err_output


def logger_get_logger(log_file=None, temp_log_file=None, console=True, debug=False, multiprocessing_formatter=False):
    # If a name is given to getLogger, than modules can't log to the root logger
    f = ContextFilterWorstLevel()
    _logger = logging.getLogger()

    # Remove earlier handlers if exist
    while _logger.handlers:
        _logger.handlers.pop()

    _logger.addFilter(f)
    if debug is True:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.INFO)
    if console:
        console_handler = logger_get_console_handler(multiprocessing_formatter=multiprocessing_formatter)
        if console_handler:
            _logger.addHandler(console_handler)
    if log_file is not None:
        file_handler, err_output = logger_get_file_handler(log_file,
                                                           multiprocessing_formatter=multiprocessing_formatter)
        if file_handler:
            _logger.addHandler(file_handler)
            _logger.propagate = False
            if err_output is not None:
                print(err_output)
                _logger.warning('Failed to use log file [%s], %s.', log_file, err_output)
    if temp_log_file is not None:
        if os.path.isfile(temp_log_file):
            try:
                os.remove(temp_log_file)
            except OSError:
                logger.warning('Cannot remove temp log file [%s].' % temp_log_file)
        file_handler, err_output = logger_get_file_handler(temp_log_file,
                                                           multiprocessing_formatter=multiprocessing_formatter)
        if file_handler:
            _logger.addHandler(file_handler)
            _logger.propagate = False
            if err_output is not None:
                print(err_output)
                _logger.warning('Failed to use log file [%s], %s.', log_file, err_output)
    return _logger


# Platform specific functions ###################################################

def get_os():
    if os.name == 'nt':
        return 'Windows'
    elif os.name == 'posix':
        result = os.uname()[0]

        if result.startswith('MSYS_NT-'):
            result = 'Windows'

        return result
    else:
        raise OSError("Cannot get os, os.name=[%s]." % os.name)


def python_arch():
    if get_os() == "Windows":
        if 'AMD64' in sys.version:
            return 'x64'
        else:
            return 'x86'
    else:
        return os.uname()[4]


def is_64bit_python():
    # We detect Python verison and not OS version here
    return sys.maxsize > 2 ** 32


# Standard functions ############################################################

def time_is_between(current_time, time_range):
    """
    https://stackoverflow.com/a/45265202/2635443
    print(is_between("11:00", ("09:00", "16:00")))  # True
    print(is_between("17:00", ("09:00", "16:00")))  # False
    print(is_between("01:15", ("21:30", "04:30")))  # True
    """

    if time_range[1] < time_range[0]:
        return current_time >= time_range[0] or current_time <= time_range[1]
    return time_range[0] <= current_time <= time_range[1]


def bytes_to_string(bytes_to_convert):
    """
    Litteral bytes to string
    :param bytes_to_convert: list of bytes
    :return: resulting string
    """
    if not bytes_to_convert:
        return False
    try:
        return ''.join(chr(i) for i in bytes_to_convert)
    except ValueError:
        return False


def check_for_virtualization(product_id):
    """
    Tries to find hypervisors, needs various WMI results as argument, ie:
    product_id = [computersystem.Manufacturer, baseboard.Manufacturer, baseboard.Product,
              bios.Manufacturer, bios.SerialNumber, bios.Version]

    :param product_id (list) list of strings that come from various checks above
    :param return (bool)

    Basic detection
    Win32_ComputerSystem.Model could contain 'KVM'
    Win32_BIOS.Manufacturer could contain 'XEN'
    Win32_BIOS.SMBIOSBIOSVersion could contain 'VBOX', 'bochs', 'qemu', 'VirtualBox', 'VMWare' or 'Hyper-V'

    ovirt adds oVirt to Win32_computersystem.Manufacturer (tested on Win7 oVirt 4.2.3 guest)
    HyperV may add 'Microsoft Corporation' to Win32_baseboard.Manufacturer
        and 'Virtual Machine' to Win32_baseboard.Product (tested on Win2012 R2 guest/host)
    HyperV may add 'VERSION/ VRTUAL' to Win32_BIOS.SMBIOSBIOSVersion (tested on Win2012 R2 guest/host)
        (yes, the error to 'VRTUAL' is real)
    VMWare adds 'VMWare to Win32_BIOS.SerialNumber (tested on Win2012 R2 guest/ VMWare ESXI 6.5 host)
    Xen adds 'Xen' to Win32_BIOS.Version (well hopefully)
    """

    for p_id in product_id:
        if type(p_id) == str:
            # First try to detect oVirt before detecting Qemu/KVM
            if re.search('oVirt', p_id, re.IGNORECASE):
                return True, 'oVirt'
            elif re.search('VBOX', p_id, re.IGNORECASE):
                return True, 'VirtualNox'
            elif re.search('VMWare', p_id, re.IGNORECASE):
                return True, 'VMWare'
            elif re.search('Hyper-V', p_id, re.IGNORECASE):
                return True, 'Hyper-V'
            elif re.search('Xen', p_id, re.IGNORECASE):
                return True, 'Xen'
            elif re.search('KVM', p_id, re.IGNORECASE):
                return True, 'KVM'
            elif re.search('qemu', p_id, re.IGNORECASE):
                return True, 'qemu'
            elif re.search('bochs', p_id, re.IGNORECASE):
                return True, 'bochs'
            # Fuzzy detection
            elif re.search('VRTUAL', p_id, re.IGNORECASE):
                return True, 'HYPER-V'
    return False, 'Physical / Unknown hypervisor'



def rot13(string):
    """
    Rot13 for only A-Z and a-z characters
    """
    try:
        return ''.join(
            [chr(ord(n) + (13 if 'Z' < n < 'n' or n < 'N' else -13)) if ('a' <= n <= 'z' or 'A' <= n <= 'Z') else n for
             n in
             string])
    except TypeError:
        return None


def tmbscfe(string):
    """
    The Most Basic Symetric Cipher Function Ever
    Reverse string case and reverse string itself and rot13 it's alphabetical chars
    :param string:
    :return:
    """
    try:
        return ''.join(c.lower() if c.isupper() else c.upper() for c in reversed(rot13(string)))
    except TypeError:
        return None


def revac(b, root=True):
    """
    Another very basic symetric cipher function that just makes sure keys don't get stored in cleartext

    :param b: (bytes) byte sequence to cipher
    :param root: (bool) used for recursion, do not give any arguments
    :return: (bytes) ciphered byte sequence
    """
    l = len(b)
    hl = int(l / 2)
    if l == 1:
        return b
    elif not l % 2 and l <= 2:
        result = [b[1], b[0]]
    elif not l % 3 and l <= 3:
        result = [b[2], b[1], b[0]]
    elif not l % 4:
        result = revac(b[0:hl], root=False) + revac(b[hl:l], root=False)
    elif not l % 6:
        result = revac(b[0:hl], root=False) + revac(b[hl:l], root=False)
    else:
        result = revac(b[0:hl], root=False) + [b[hl]] + revac(b[hl + 1:l], root=False)
    if root:
        return bytes(result)
    else:
        return result


# Restrict number n between minimum and maximum
restrict_numbers = lambda n, n_min, n_max: max(min(n_max, n), n_min)


def _selftest():
    print('Example code for %s, %s, %s' % (__intname__, __version__, __build__))

    _logger = logger_get_logger()
    assert isinstance(_logger, logging.Logger), 'Logger class was not created'

    os_ = get_os()
    print('Current OS: %s' % os_)
    assert isinstance(os_, str), 'get_os check failed'

    py_arch = python_arch()
    print('Current python arch: %s' % py_arch)
    assert py_arch == 'x86' or py_arch == 'x64', 'python_arch test failed'

    assert isinstance(is_64bit_python(), bool), 'is_64bit_python check failed'

    assert time_is_between("11:00", ("09:00", "16:00")) is True, 'time_is_between failed N°1'
    assert time_is_between("17:00", ("09:00", "16:00")) is False, 'time_is_between failed N°2'
    assert time_is_between("01:15", ("21:30", "04:30")) is True, 'time_is_between failed N°3'

    is_virt, _ = check_for_virtualization(['Xen'])
    assert is_virt  == True, 'Virtualization check failed'

    b = b'\x65\x66\x67'
    assert bytes_to_string(b) == 'efg', 'bytes_to_string failed'

    msg = 'MessageIn A 64 years old bottle !'
    rot13_msg = rot13(msg)
    assert msg == rot13(rot13_msg), 'rot13 failed'

    tmbscfe_msg= tmbscfe(msg)
    assert msg == tmbscfe(tmbscfe_msg), 'tmbscfe failed'

    revac_msg = revac(msg.encode(encoding='utf-8'))
    assert msg == revac(revac_msg).decode(encoding='utf-8'), 'revac failed'


if __name__ == '__main__':
    _selftest()