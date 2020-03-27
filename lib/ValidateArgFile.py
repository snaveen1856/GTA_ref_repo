import os
import sys
from lib.IntConfig import notify
from os.path import expanduser
import yaml
from lib.exceptions import TestBuildTypeException
from lib import logger
from lib.IntConfig import EmailNotification,Message
from lib.utilities import fetch_data_from_testenvdata
errormsg = ""


def validate_config(value, lineno=None):
    """
    Check if the config file is yaml or not.

    - **parameters**, **types**, **return** and **return types**::

      :param value: config.yaml info from argfile
      :type value: string
      :param lineno: line no of the config.yaml info from argfile
      :type lineno: int
      :return: Returns errormsg
      :rtype: string

    """
    global errormsg
    if value != "None" and ".yaml" not in value:
        if lineno:
            msg = ("In Argfile at line number %s "
                   "config file is not yaml file." %lineno)
        else:
            msg = "Please provide '.YAML' file for -c option."
        notify.message(msg)
        errormsg = errormsg + "\n\n" + msg
    if not lineno:
        return errormsg

def validate_duration(value, lineno=None):
    """
    Check if the duration value is provided in correct format.

    - **parameters**, **types**, **return** and **return types**::

      :param value: duration value from argfile
      :type value: string
      :param lineno: line no of the duration value from argfile
      :type lineno: int
      :return: Returns errormsg
      :rtype: string

    """
    global errormsg
    if value != "None" and "c" not in value.lower() and "m" not in value.lower():
        if lineno:
            msg = ("In Argfile at line number %s "
               "duration must be mentioned in Cycles or "
               "Minutes i.e 5C or 5M" %lineno)
        else:
            msg = "duration must be mentioned in Cycles or Minutes i.e 5C or 5M"
        notify.message(msg)
        errormsg = errormsg + "\n\n" + msg
    num = value[:-1]
    if not num.isdigit():
        if lineno:
            msg = ("In Argfile at line %s provided duration is not in "
                   "correct format. it has to be like 5C or 12M" %lineno)
        else:
            msg = ("provided duration is not in correct format. "
                   "It has to be like 5C or 12M")
        notify.message(msg)
        errormsg = errormsg + "\n\n" + msg
        if not lineno:
            return errormsg
        else:
            return
    num = int(num)
    if "c" in value.lower():
        if num <= 0:
            if lineno:
                msg = ("In Argfile at line %s "
                       "Number of cycles cannot be 0 or less than 0." %lineno)
            else:
                msg = "Number of cycles cannot be 0 or less than 0"
            notify.message(msg)
            errormsg = errormsg + "\n\n" + msg
        if num > 500:
            if lineno:
                msg = ("In Argfile at line %s "
                       "Number of cycles cannot be more than 500" %lineno)
            else:
                msg = "Number of cycles cannot be more than 500"
            notify.message(msg)
            errormsg = errormsg + "\n\n" + msg
    else:
        if num <= 0:
            if lineno:
                msg = ("In Argfile at line %s "
                       "Number of minutes cannot be 0 or less than 0." %lineno)
            else:
                msg = "Number of minutes cannot be 0 or less than 0."
            notify.message(msg)
            errormsg = errormsg + "\n\n" + msg
        if num > 10080:
            if lineno:
                msg = ("In Argfile at line %s "
                       "Number of minutes cannot be more than a week." %lineno)
            else:
                msg = ("Number of minutes cannot be more than a week.")
            notify.message(msg)
            errormsg = errormsg + "\n\n" + msg
    if not lineno:
        return errormsg

def validateandparseargfile(testsfile):
    """
    Check if data in argfile is in correct format.

    - **parameters**, **types**, **return** and **return types**::

      :param testsfile: path of argfile
      :type testsfile: string
      :return: Returns errormsg and list of sutas commands
      :rtype: tuple

    """
    global errormsg
    os.environ['argfile'] = testsfile
    try:
        with open(testsfile, "r") as argfile:
            tests = argfile.read().strip().splitlines()
    except IOError:
        if not '.txt' in testsfile:
            msg = ("Provide the file {} with .txt extension or "
                   "checkwhether the file exists or not".format(testsfile))
        else:
            msg = "Check whether the file exists or not."
        raise Exception(msg)
    argv = []
    cmd = None
    for line in tests:
        lineno = tests.index(line) + 1
        line = line.split('\t')
        line = [word for word in line if word!='']
        if len(line) != 5:
            msg = ("In Arg file at line %s "
                   "extra argument is provided."
                   "It must be in below format.\n"
                   "Each line must contain <robot file path> "
                   "<config.yaml file> <Jira testid>   <Duration>    <testtype>\n"
                   "ts1.robot    ts1.yaml    TM-121    5C     MPTC\n"
                   "ts2.robot    ts2.yaml    None      60M    Regression\n"
                   "ts3.robot    None        None      None   None\n"
                   "ts4.robot    ts4.yaml    TM-124    None   None\n"
                   "config file, jira id, duration and testtype are optional "
                   "i.e you have to replace it with None if not used.\nAll must be seperated with tab space" %lineno)
            notify.message(msg)
            errormsg = errormsg + "\n\n" + msg
            raise Exception(errormsg)
        if line[1] != 'None':
            validate_config(line[1], lineno)
        if line[3] != 'None':
            validate_duration(line[3], lineno)
        if len(line) == 5:
            if line[3] != 'None' and "-p" in sys.argv:
                if sys.argv[sys.argv.index("-p")+1].lower() == "true":
                    msg = ("SUTAS cannot run tests in parallel when duration "
                           "is mentioned in argfile")
                    notify.message(msg)
                    errormsg = errormsg + "\n\n" + msg
                    break
            cmd = [sys.argv[0], "execute", ]
            if not line[0]:
                msg = ("Argfile doesn't contain testsuite "
                       "in one of the lines.")
                notify.message(msg)
                errormsg = errormsg + "\n\n" + msg
            else:
                cmd.extend(["-s", line[0]])
            if line[1] != 'None':
                cmd.extend(["-c", line[1]])
            if line[2] != 'None':
                cmd.extend(["-j", line[2]])
            if line[3] != 'None':
                cmd.extend(["-d", line[3]])
            if line[4].lower() == 'none':
                raise Exception("TestBuildType must be specified in the argfile for the line {}".format(line))
            if line[4] != 'None':
                line[4] = line[4].replace('"','')
                line[4] = line[4].replace("'",'')
                TBTypes = fetch_data_from_testenvdata('TestBuildTypes')
                try:
                    if line[4] not in TBTypes:
                        raise TestBuildTypeException
                except TestBuildTypeException as err:
                    mailobj = EmailNotification().emailobj()
                    body = "TestBuildType must be specified from one of the following {}".format(TBTypes)
                    mailobj.send_mail_when_failed(body)
                    print(TestBuildTypeException(body))
                    sys.exit(1)
                cmd.extend(["-l", line[4]])
        argv.append(cmd)
    return (errormsg, argv)
