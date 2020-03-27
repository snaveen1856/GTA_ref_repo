"""
This module configures stream handler and file handlers. Adds these handlers
into logging instance and returns logger instance.
"""
import logging
import yaml
import os
from os.path import expanduser

LOG_FORMAT     = '%(asctime)s - %(levelname)-8s %(message)s'
LOG_NAME       = 'sutas'
LOG_LEVELS = {'debug': logging.DEBUG,
              'error': logging.ERROR,
              'warn': logging.WARNING,
              'info': logging.INFO}

def _get_logfile_loglevel():
    """
    Return the logfile path from user_info.yaml file.
    
    - **parameters**, **types**, **return** and **return types**::
    
          :return: Value of Logfile key from user_info.yaml file is returned.
          :rtype: String
    """
    filepath = os.path.join(expanduser('~'), "global_conf.yaml")
    with open(filepath , 'r') as f:
            f_data = yaml.load(f, Loader=yaml.FullLoader)
    if "LogLevel" in list(f_data.keys()): 
        return (os.environ["logpath"], f_data["LogLevel"])
    else:
        return (os.environ["logpath"], "info")

def getLogger(console):
    """
    Create, configure and return logger for logging.
    
    Creates logger using python logging module.
    Configures stream handler and file handler.
    Returns logger with stream and file handlers added to it.
    
    - **parameters**, **types**, **return** and **return types**::
    
          :return: Value of Logfile key from user_info.yaml file is returned.
          :rtype: String    
    """
    if "logpath" not in os.environ:
        return None
    LOG_FILE, LEVEL = _get_logfile_loglevel()
    LEVEL = LOG_LEVELS[LEVEL]
    log = logging.getLogger(LOG_NAME)
    if len(log.handlers) > 0:
        log.handlers = []
    log.setLevel(LEVEL)
    log_formatter = logging.Formatter(LOG_FORMAT)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(LEVEL)
        log.addHandler(stream_handler)

    file_handler_info = logging.FileHandler(LOG_FILE)
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(LEVEL)
    log.addHandler(file_handler_info)
    return log
