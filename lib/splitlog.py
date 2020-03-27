import os
from lib.utilities import get_data_from_yaml
from lib import logger

def get_individual_log(tcname):
    """
    This function creates individual TC logs from testsuite log.
    
    Sutas generates whole testsuite log. From this testsuite log
    individual test case logs will be created.
    
    - **parameters**, **types**, **return** and **return types**::
    
        :param tcname: Testcase name with which testsuite log will
                       be parsed and created individual log.
        :type tcname: String
        :return: Path of created test case log
        :rtype: String
    """
    str = tcname + " execution started by sutas"
    logfile = os.environ["logpath"]
    logpath = os.path.dirname(logfile)
    startline = None
    startline = _get_line_number(logfile, str)
    if startline is None:
        logger.warn("Cannot find individual TC log for %s" %tcname)
        return logfile
    with open(logfile, 'r') as suitelog:
        log_data = suitelog.readlines()
    line = startline - 1
    log_data = log_data[line:]
    tclog = os.path.join(logpath, tcname+".log")
    fp = open(tclog, "w")
    fp.write(log_data[0])
    for line in log_data[1:]:
        if "execution started by sutas" in line:
            break
        fp.write(line)
    fp.close
    return tclog

def _get_line_number(logfile, str):
    """
    Returns the line number where the string is found in the file.

    - **parameters**, **types**, **return** and **return types**::
    
        :param logfile: testsuite logfile path
        :param str: String to be searched in the file
        :return: Returns the line number where the string is found
        :rtype: int

    """
    with open(logfile, 'r') as suitelog:
        log_data = suitelog.readlines()
        for num, line in enumerate(log_data, 1):
            if str in line.decode('utf-8'):
                    return num

