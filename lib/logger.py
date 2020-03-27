"""
This module gets the logger instance from sutaslogger and
writes the message in to file with mentioned log level.
"""
import logging
from lib.sutaslogger import getLogger
import sys

LOG_LEVELS = {
    'CRITICAL': logging.CRITICAL,
    'DEBUG':    logging.DEBUG,
    'ERROR':    logging.ERROR,
    'WARN':  logging.WARNING,
    'INFO':     logging.INFO,
}
flag = False

def write(msg, level='INFO', also_console=False, callname=None):
    """
    Writes the message to the log file using the given level.

    - **parameters**, **types**, **return** and **return types**::

          :param msg: Message to be logged
          :param level: Log level. default level is INFO.
          :param also_console: If also_console is True then message will be
                               displayed on to console.
          :type msg: String
          :type Level: String
          :type also_console: boolean
    """
    logger = getLogger(also_console)
    if logger:
        level = LOG_LEVELS[level]
        #if type(msg) is str:
            #msg = msg.strip("\n")
        msg = callname + ": " + str(msg)
        logger.log(level, msg)
    else:
        from robot.api import logger
        global flag
        if not flag:
            logger.warn("Using robot framework logger since tests are not run using SUTAS.")
            flag = True
           
        if level.lower() == "info":
            logger.info(msg, also_console=also_console)
        elif level.lower() == "debug":
            logger.debug(msg)
        elif level.lower() == "warn":
            logger.warn(msg)
        elif level.lower() == "error":
            logger.error(msg)

def debug(msg, console=True):
    """
    Writes the message to the log file using the ``DEBUG`` level.

    - **parameters**, **types**, **return** and **return types**::

          :param msg: Message to be logged
          :type msg: String

    """
    callname = sys._getframe().f_back.f_code.co_name
    write(msg, level='DEBUG',also_console=console, callname=callname)


def info(msg, console=True):
    """
    Writes the message to the log file using the ``INFO`` level.

    - **parameters**, **types**, **return** and **return types**::

          :param msg: Message to be logged
          :param console: if conosle is True then msg will be displayed on
                          to console.
          :type msg: String
          :type console: Boolean
    """
    callname = sys._getframe().f_back.f_code.co_name
    write(msg, level='INFO', also_console=console, callname=callname)


def warn(msg, console=True):
    """
    Writes the message to the log file using the ``WARN`` level.

    - **parameters**, **types**, **return** and **return types**::

          :param msg: Message to be logged
          :type msg: String
    """
    callname = sys._getframe().f_back.f_code.co_name
    write(msg, level='WARN', also_console=console,callname=callname)


def error(msg, console=True):
    """
    Writes the message to the log file using the ``ERROR`` level.

    - **parameters**, **types**, **return** and **return types**::

          :param msg: Message to be logged
          :type msg: String
    """
    callname = sys._getframe().f_back.f_code.co_name
    write(msg, level='ERROR',also_console=console, callname=callname)
