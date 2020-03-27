"""
This module contains utility methods.
"""
import os
from os.path import expanduser
import site
import re
import time
from random import randint
import yaml
from lib import logger
from distutils import sysconfig
globdata = None
userdata = None


def cleanconfig():
    """
        Removes some values from glob_conf.yaml file.
    """
    globalfilepath = os.path.join(os.path.expanduser('~'), "global_conf.yaml")
    data = get_data_from_yaml(globalfilepath)
    keys = ["TestStatus", "Logfile", "Configfile"]
    for key in keys:
        if key in data:
            data.pop(key)
    dump_data_into_yaml(globalfilepath, data, mode="w")


def get_data_from_yaml(filepath):
    """
    Get dictionary out of yaml file and return it.

    - **parameters**, **types**, **return** and **return types**::

          :param filepath: Yaml file path
          :type filepath: String
          :return: Returns data of yaml file as dictionary
          :rtype: dictionary
    """
    global globdata
    global userdata
    userinfo = False
    glob = False
    if "user_info" in filepath:
        userinfo = True
        if userdata:
            return userdata

    if "global_conf" in filepath:
        glob = True
        if globdata:
            return globdata

    if os.path.exists(filepath):
        with open(filepath, 'r') as yaml_file:
            data = yaml.load(yaml_file, Loader=yaml.FullLoader)
        if userinfo:
            userdata = data
        elif glob:
            globdata = data
        return data
    else:
        raise Exception(
            "user_info not avaialable. run 'sutas user_setup'\
             before exescuting test suite")


def dump_data_into_yaml(filepath, data, mode="a"):
    """
    Get dictionary out of yaml file and return it.

    - **parameters**, **types**, **return** and **return types**::

          :param filepath: Yaml file path
          :param data: Data which needs to be added into Yaml file
          :param mode: In which mode file should be opened.
          :type filepath: String
          :type data: Dictionary
          :type mode: String
    """
    global globdata
    global userdata

    with open(filepath, mode) as yamlfile:
        yaml.dump(data, yamlfile,
                  default_flow_style=False)
    if "global_conf" in filepath:
        globdata = None
    elif "user_info" in filepath:
        userdata = None
    get_data_from_yaml(filepath)


def create_log_file(args):
    """
    Creates log file for logging sutas execution.

    If user runs sutas user_setup
      log file named sutas_usersetup appended with time stamp will be generated.

    If user runs test suite
      log file named testsuite appended with timestamp will be generated.


    - **parameters**, **types**, **return** and **return types**::

        :param args: Args from the sutas command
        :type: args: list
        :return outputdir: directory path of the log file.
    """
    args = args[1:]
    sutasfolder = os.path.join(os.path.expanduser('~'), "Sutas_Logs")
    if not os.path.isdir(sutasfolder):
        os.mkdir(sutasfolder)
    if "execute" in args:
        testsuite = os.path.basename(args[args.index("-s") + 1]).split(".")[0]
        num = randint(111, 999)
        outputdir = os.path.join(sutasfolder,
                                 testsuite + "_" + str(num) + "_" +
                                 time.strftime("%Y%b%d_%H%M%S"))
        os.mkdir(outputdir)
        logfile = testsuite + time.strftime("%Y%b%d_%H%M%S") + ".log"
        logpath = os.path.join(outputdir, logfile)
        with open(logpath, "w+") as log:
            log.write("SUTAS logging Started\n")
    else:
        logfile = "sutas_usersetup" + time.strftime("%Y%b%d_%H%M%S") + ".log"
        logpath = os.path.join(sutasfolder, logfile)
        with open(logpath, "w+") as log:
            log.write("SUTAS User Setup Started\n")
        outputdir = None
    os.environ["logpath"] = logpath
    return outputdir


def _changetransistion(conn, tckey, tostate):
    transitions = conn.transitions(tckey)
    for transition in transitions:
        if transition['name'].lower() == tostate:
            conn.transition_issue(tckey, str(transition['id']))
            break


def make_transitions(conn, test_case):
    """
    Transitions
    """
    status = test_case.fields().status.name.lower()
    msg = 'Current status of testcase %s is %s'%(test_case,status)
    logger.warn(msg)
    if status == 'failed' or status == 'skipped' or status in ['todo','to do']:
        if status == 'failed' or status == 'skipped':
            _changetransistion(conn, test_case.key, 'back to todo')
        _changetransistion(conn, test_case.key, 'ready to run')
        _changetransistion(conn, test_case.key, 'running')
        _changetransistion(conn, test_case.key, 'test in progress')
    elif status == 'ready to run':
        _changetransistion(conn, test_case.key, 'running')
    elif status in ['running', 'test in progress']:
        msg = test_case.fields().issuetype.name + ' is in ' + status + ' State'
        logger.warn(msg)
    else:
        logger.warn("Unknown Status...")

def check_diskusage(conn):
    '''checks the disk space on a server
        - **parameters**, **types**, **return** and **return types**::

        :param conn: ssh connection obj.
        :type kwargs: ssh object
            
    '''
    
    rtcode,stdout,stderr = conn.exec_command('df -h /')
    if stderr.read() == '':
        out = stdout.read().strip().split('\n')
        used = int(out[-1].split()[-2][:-1])
        if used > 75:
            msg = 'used disk space is ' + str(used) +'%. Available disk space is less than 75%. please free up the disk space'
            logger.warn(msg)
            return True
        else:
            msg = str(used) + '% of disk space is utilized.'
            logger.warn(msg)
    
def getsutasversion():
    site_packages_path = sysconfig.get_python_lib()
    filepath = os.path.join(site_packages_path, 'easy-install.pth')
    try:
        with open(filepath) as fp:
            data = fp.read()
    except IOError:
        site_packages_path = site.getsitepackages()
        filepath = os.path.join(site_packages_path[0], 'easy-install.pth')
        with open(filepath) as fp:
            data = fp.read()
    pattern = re.compile(r'[\d.]+',re.IGNORECASE)
    version = re.findall(pattern,data)
    return version[-2]

def fetch_data_from_testenvdata(key):
    envfile = os.path.join(expanduser('~'),'testenvdata.yaml')
    if os.path.exists(envfile):
        with open(envfile,'r') as fileobj:
            data = yaml.load(fileobj, Loader=yaml.FullLoader)
        return data[key]
    else:
        raise Exception("SUTAS is not installed correctly.Please reinstall and run")
