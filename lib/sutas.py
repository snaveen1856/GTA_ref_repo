#!/usr/bin/env python
"""
SUTAS file for running sutas framework
"""

import argparse
import os
import re
from os.path import expanduser
import sys
import datetime
import time
from shutil import copyfile
import platform
import socket
import traceback
from multiprocessing import Process
import psutil
import yaml
from lib.utilities import (get_data_from_yaml, getsutasversion,
                           create_log_file, make_transitions,fetch_data_from_testenvdata)
from lib import logger
from lib.ValidateArgFile import (validateandparseargfile,
                                 validate_config,
                                 validate_duration)
from lib.ParseAndRaiseBug import ParseAndRaiseBug
from lib.Jiralib import Jiralib
from lib.IntConfig import notify
from lib.ValidateUserConfig import ValidateUserConfig
from lib.TestManagement import TestManagement
from lib.TestArtifact import TestArtifact
from lib.usersetup import UserSetup
from lib.validaterobotfile import (ValidateRobotFile, IncorrectRobotfile,
                                   DependencyException)
from lib.jenkinsetup import jenkinsetup
from lib.db_utils import Db_utils
from lib.models import test_execution, test_suite, projects, users, test_case, fix_version
from robot.run import run_cli
from lib.exceptions import UserException,TestBuildTypeException
from lib.performancecalc import perfcompare, process_file, findmaxvaluesfrombenchmark, getdatafromfile
from jira import JIRA, JIRAError
from robot.parsing.model import TestData
from lib.IntConfig import EmailNotification,Message

suite_details = {}
output_dir = None
DATA = {}
glob_data = {}
globalfilepath = None
db_util_obj = None
subject = ''


class Sutas(object):
    """
    Class for SUTAS Execution
    """

    def __init__(self, args):
        """
        Sutas Class Constructor

        - **parameters**, **types**, **return** and **return types**::

            param args: Arguments passed while running SUTAS framework
            type args: List
        """
        msg = ("sutas command usage:\n"
               "\nRun user_setup to create config files\n"
               "\n\tsutas user_setup\n"
               "\nRun create_benchmark to create benchmark file\n"
               "\n\tsutas create_benchmark -o <output.xml>\n"
               "\n\nRun tests from tests.txt file\n"
               "\ntests.txt file must be in below format.\n"
               "\nEach line must contain <robot file path> "
               "<config.yaml file> <Jira testid> <duration> <testtype>\n"
               "ts1.robot    ts1.yaml    TM-121    5C    MPTC\n"
               "ts2.robot    ts2.yaml    None      30M   Regression\n"
               "ts3.robot    None        None      None  None\n"
               "ts4.robot    ts4.yaml    TM-124    None  None\n"
               "\nconfig file, jira id and duration are optional\n"
               "i.e you have to replace it with None if not used.\n"
               "\n\tsutas execute -a tests.txt\n"
               "\n\nRun tests from tests.txt in parallel\n"
               "\n\tsutas execute -a tests.txt -p True\n"
               "\n\nRun one testsuite\n"
               "\n\tsutas execute -c config.yaml -s testsuite.robot\n"
               "\n\nRun testsuite and update Jira\n"
               "\n\tsutas execute -c config.yaml -s "
               "testsuite.robot -j <Jira master testuite id>\n"
               "\n\nRun single or multiple testcases\n"
               "\n\tsutas execute -c config.yaml -s "
               "testsuite.robot -t "
               "<testcasename or testcasenames seperated by comma>\n"
               "\n\tsutas execute -c config.yaml -s "
               "testsuite.robot -l "
               "<tag or tags seperated by comma>\n"
               "\n\nReruns all failed or skipped testcases\n"
               "\n\tsutas execute -c config.yaml -s "
               "testsuite.robot -t failed/skipped -i "
               "<jira cloned testsuite id>\n"
               "\n\nReRuns specified failed or all failed testcases\n"
               "\n\tsutas execute -c config.yaml -s "
               "testsuite.robot -i "
               "<jira cloned testcase id/testsuite id>\n"
               "\n\nRun testsuite and Compares with benchmark times mentioned in the yaml.\n"
               "\n\tsutas execute -b benchmark.yaml -s testsuite.robot\n")
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=msg)
        subparsers = parser.add_subparsers()
        parser_b = subparsers.add_parser('execute', help='SUTAS run')
        parser_b.add_argument("-s", "--tcsuite",
                              help="specify test suite name to run")
        parser_b.add_argument("-b", "--benchmark",
                              help="specify xml file to get benchmark values")
        parser_b.add_argument("-c", "--configfile",
                              help="provide the config file full path")
        parser_b.add_argument("-t", "--testcasename",
                              help="provide the testcase name")
        parser_b.add_argument("-j", "--jira_test_suit_id",
                              help="provide Cloned test suite id from JIRA")
        parser_b.add_argument("-l", "--label",
                              help="provide test case tag from testsuite")
        parser_b.add_argument("-a", "--argfile",
                              help="provide path of the tests file which \
                              contains what testsuites to be executed.")
        parser_b.add_argument("-d", "--duration",
                              help="duration to run the tests.")
        parser_b.add_argument("-e", "--environment",
                              help="environment and tenanat info on which tests to be run.")
        parser_b.add_argument("-p", "--parallel",
                              default='False', choices=['True', 'False', 'true', 'false'],
                              help="provide Cloned test suite id from JIRA")
        parser_b.add_argument("-i", "--clone id",
                              help="cloned test suite id/testcaseid for rerun")
        parser_a = subparsers.add_parser('user_setup', help='creates \
                                         configuration file')
        parser_a.add_argument("--symmetrickey",
                              help="Specify symmetric key")
        parser_a.add_argument("--raisebugs",
                              help="Enable/Disable jira yes/no")
        parser_a.add_argument("--jiraurl",
                              help="specify jira url")
        parser_a.add_argument("--jirausr",
                              help="specify jira url")
        parser_a.add_argument("--jirapwd",
                              help="Provide jira pwd")
        parser_a.add_argument("--jira_affect_version",
                              help="specify jira affect version")
        parser_a.add_argument("--jiraenv",
                              help="specify jira environment")
        parser_a.add_argument("--jiraproj",
                              help="specify jira url")
        parser_a.add_argument("--jira_watcher",
                              help="specify jira watcher")
        parser_a.add_argument("--jirabugpriority",
                              help="specify jira bug priority (1:Critcical,2:High,3:Medium,4:Low,5:Trivial)", choices=['1', '2', '3', '4', '5'])
        parser_a.add_argument("--jirabugseverity",
                              help="specify jira bug severity (1:Critcical,2:Major,3:Moderate,4:Low,5:Trivial)", choices=['1', '2', '3', '4', '5'])
        parser_a.add_argument("--slack",
                              help="Enable/disable slack notification yes/no")
        parser_a.add_argument("--slackusr",
                              help="Provide Slack username")
        parser_a.add_argument("--slacktoken",
                              help="Provide Slack token")
        parser_a.add_argument("--slackchannel",
                              help="Provide Slack channel name")
        parser_a.add_argument("--teamsnotifications",
                              help="yes/no microsoft teams notifications")
        parser_a.add_argument("--teamsurl",
                              help="Incomming webhook url of the teams"
                              "channel")
        parser_a.add_argument("--loglevel",
                              help="Provide log info")
        parser_a.add_argument("--emailnotifications",
                              help="yes/no email notifications")
        parser_a.add_argument("--emails",
                              help="Specify recipients emails")
        parser_a.add_argument("--send_mail_only_if_failed",
                              help="Send mail only if testcases are passed")
        parser_a.add_argument("--validateemails",
                                  help="yes/no to validate emails")
        parser_a.add_argument("--smtpip",
                              help="SMTP IP")
        parser_a.add_argument("--smtpport",
                              help="SMTP port")
        parser_a.add_argument("--consolidatedmail",
                              help="use this option for consolidated mail")
        parser_a.add_argument("--enabledatabase",
                              help="yes/no database")
        parser_a.add_argument("--dbusername",
                              help="username of DB")
        parser_a.add_argument("--dbpassword",
                              help="password of DB user")
        parser_a.add_argument("--dbserverip",
                              help="IP of DB server")
        parser_a.add_argument("--serverostype",
                              help="ostype of DBserver")
        parser_a.add_argument("--dbserveruser",
                              help="username of DB")
        parser_a.add_argument("--dbserverpwd",
                              help="password of DB server user.")
        parser_a.add_argument("--dbprune",
                              help="use this option to prune database.")
        parser_a.add_argument("--databasename",
                              help="name of DB")
        parser_a.add_argument("--enabletestmanagement",
                              help="yes/no EnableTestManagement")
        parser_a.add_argument("--tm_project",
                              help="specify jira test management project name")
        parser_a.add_argument("--sprintnumber",
                              help="provide sprint number to clone "
                              "those tests only")
        parser_a.add_argument("--fixversion",
                              help="provide fix version to update "
                              "suite/tests")
        parser_a.add_argument("--enablepushtestartifacts",
                              help="yes/no EnablePushingTestArtifacts")
        parser_a.add_argument("--testaritfactsserverip",
                              help="IP of testaritfacts server")
        parser_a.add_argument("--testaritfactsserveruser",
                              help="username of testaritfacts")
        parser_a.add_argument("--testaritfactsserverpwd",
                              help="password of testaritfacts server user.")
        parser_a.add_argument("--testenvironment",
                              help="provide test environment name as projectname_env, e.g msaws_qa ")
        parser_c = subparsers.add_parser('create_benchmark', help='creates \
                                             benchmark file')
        parser_c.add_argument('-o', "--outputxml",
                              help='provide output.xml file')
        parser_d = subparsers.add_parser('version', help='displays \
                                                 sutas version')

        args = parser.parse_args()
        self.args = args
        self.yam = None
        if 'execute' in sys.argv:
            if vars(self.args)['label']:
                vars(self.args)['label'] = vars(self.args)['label'].replace('"','')
                vars(self.args)['label'] = vars(self.args)['label'].replace("'",'')
            suite = vars(self.args)['tcsuite']
            if suite:
                if ":" in suite or suite.startswith("/"):
                    self.robo_file = suite
                else:
                    self.robo_file = os.path.join(os.getcwd(), suite)
                os.environ['robosuitepath'] = self.robo_file
                robosuitepath = os.environ['robosuitepath']
                try:
                    suite = TestData(parent=None, source=robosuitepath)
                except:
                    raise Exception("Robot suite {} doesn't exist".format(self.robo_file))
                robotctagids = []
                robotcnames = []
                for testcase in suite.testcase_table:
                    robotcnames.append(testcase.name.lower())
                    robotctagids.append(testcase.tags.value)
                robotcdict = dict(list(zip(robotcnames,robotctagids)))
                os.environ.__dict__['robotcdict'] = {}
                os.environ.__dict__['robotcdict'] = robotcdict

    def validate_args(self):
        """
        To validate arguments.
        """
        start_time = datetime.datetime.now()
        os.environ['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        if 'version' in sys.argv:
            version = getsutasversion()
            logger.info(version)
            sys.exit()
        # call Usersetup method if user_setup is provided to sutas command
        if "user_setup" in sys.argv:
            # if only user_setup is provided then call UserSetup
            # method which will prompt user for few details.
            if len(sys.argv[1:]) == 1:
                UserSetup()
                sys.exit()
            # if more options are provided with user_setup then jenkinssetup
            # method is called. More option for user_setup can be found by
            # running "sutas user_setup -h" command.
            else:
                jenkinsetup(self.args)
                sys.exit()
        # below script is executed when sub command "create_benchmark" is used
        if "create_benchmark" in sys.argv:
            if '-o' in sys.argv:
                benchmarkfile = os.path.join(expanduser('~'), "benchmark.yaml")
                process_file(os.path.abspath(
                    vars(self.args)['outputxml']), benchmarkfile)
                benchmarkdata = getdatafromfile(benchmarkfile)
                benchmarkdata = findmaxvaluesfrombenchmark(benchmarkdata)
                with open(benchmarkfile, 'w') as benchdata:
                    yaml.dump(benchmarkdata, benchdata,
                              default_flow_style=False)
                msg = 'Created benchmark file at {}'.format(benchmarkfile)
                logger.warn(msg)
                sys.exit()
            else:
                logger.warn('provide a valid option')
                self.help(sys.argv)
        # if execute command is used then it checks and validates
        # whether correct options are used.
        if "execute" in sys.argv:
##            if "-a" in sys.argv and "-p" not in sys.argv and \
##               len(sys.argv[2:]) > 2:
##                logger.warn("When -a (Argfile) is provided the only other"
##                            "option it takes is -p.")
##                self.help(sys.argv)
##            if "-a" in sys.argv and "-p" in sys.argv and len(sys.argv[2:]) > 4:
##                logger.warn("When -a and -p is provided no other options "
##                            "needs to be provided.")
##                self.help(sys.argv)
            if "-j" in sys.argv and "-s" not in sys.argv:
                self.help(sys.argv)
            if "-c" in sys.argv and "-s" not in sys.argv:
                self.help(sys.argv)
            if "-l" in sys.argv:
                if "-t" in sys.argv:
                    logger.warn("Please provide either -t or -l. "
                                "Both cannot be used at a time.\n")
                    self.help(sys.argv)
                if "-i" in sys.argv:
                    logger.warn("Please provide either -t or -i. "
                                "Both cannot be used at a time.\n")
                    self.help(sys.argv)
                # if "-j" in sys.argv:
                    # logger.warn("-l cannot be used with testmanagement "
                    #"enabled -j option.\n")
                    # self.help(sys.argv)
            if "-t" in sys.argv and "-i" in sys.argv:
                if 'failed' and 'skipped' not in sys.argv:
                    msg = 'Please Provide -t option as skipped\n'
                    self.help(sys.argv)
            if "-c" in sys.argv:
                errmsg = validate_config(sys.argv[sys.argv.index("-c") + 1])
                if errmsg:
                    notify.send_message()
                    raise Exception(errmsg)
            if "-p" in sys.argv:
                if "-d" in sys.argv and sys.argv[sys.argv.index("-p") + 1].lower() == "true":
                    msg = ("\nDo not use -p with -d "
                           "when duration is mentioned, "
                           "tests cannot be run in parallel.\n")
                    raise Exception(msg)
            if "-d" in sys.argv:
                errmsg = validate_duration(sys.argv[sys.argv.index("-d") + 1])
                if errmsg:
                    notify.send_message()
                    raise Exception(errmsg)

    def show_config(self):
        """
            Checks the global_conf file and displays the feature status enabled/disabled.
        """
        msg = "Installed SUTAS version is " + getsutasversion()
        logger.warn(msg)
        notify.message(msg)
        if glob_data:
            logger.warn("Raise Bugs : %s" % glob_data.get("Raise_Bugs"))
            notify.message("Raise Bugs : %s" % glob_data.get("Raise_Bugs"))
            logger.warn("EnableDatabase : %s" % glob_data.get(
                "EnableDatabase"))
            notify.message("EnableDatabase : %s" % glob_data.get(
                "EnableDatabase"))
            logger.warn("EmailNotifications : %s" % glob_data.get(
                "EmailNotifications"))
            notify.message("EmailNotifications : %s" % glob_data.get(
                "EmailNotifications"))
            logger.warn("EnableTestManagement : %s" % glob_data.get(
                "EnableTestManagement"))
            notify.message("EnableTestManagement : %s" % glob_data.get(
                "EnableTestManagement"))
            logger.warn("SlackNotifications : %s" % glob_data.get(
                "SlackNotifications"))
            notify.message("SlackNotifications : %s" % glob_data.get(
                "SlackNotifications"))
            logger.warn("TeamsNotifications : %s" % glob_data.get(
                "TeamsNotifications"))
            notify.message("TeamsNotifications : %s" % glob_data.get(
                "TeamsNotifications"))
            logger.warn("PushTestArtifacts : %s" % glob_data.get(
                "EnableTestArtifacts"))
            notify.message("PushTestArtifacts : %s" % glob_data.get(
                "EnableTestArtifacts"))
            logger.warn("Consolidated mail : %s" %
                        glob_data.get("Consolidatedmail"))
            notify.message("Consolidated mail : %s" %
                           glob_data.get("Consolidatedmail"))
            logger.warn("LogLevel : %s" % glob_data.get("LogLevel"))
            notify.message("LogLevel : %s" % glob_data.get("LogLevel"))
        else:
            logger.warn("No configuration found in global conf file.")

    def help(self, arg):
        """
        Sutas help.

        - **parameters**, **types**, **return** and **return types**::
            param arg: commandline arguments
            type arg: List
        """
        if 'user_setup' in arg:
            os.system("sutas user_setup -h")
        elif 'execute' in arg:
            os.system("sutas execute -h")
        elif 'create_benchmark' in arg:
            os.system('sutas create_benchmark -h')
        else:
            os.system("sutas -h")
        sys.exit()

    def save_config_path(self):
        """
        Store config file path.
        """
        if "configfile" in list(vars(self.args).keys()):
            conf = vars(self.args)["configfile"]
            if conf is not None:
                if ":" in conf or conf.startswith("/"):
                    conf_file = conf
                else:
                    conf_file = os.path.join(os.getcwd(), conf)
                os.environ['ConfigFile'] = conf_file

    def run_test_suite(self, tags=None):
        """
        Run test suite.

        - **parameters**, **types**, **return** and **return types**::
            param tags: testcase tags which must be executed.
            type tags: List
        """
        robottcs = os.environ.__dict__['robotcdict']
        cmd = []
        # forming arg list to be passed to run_cli method of robot framework
        cmd.append("-d")
        # appending outputdir
        cmd.append(output_dir)
        # appending loglevel
        cmd.append("--loglevel")
        cmd.append("DEBUG")
        # adding configfile to argument list
        if vars(self.args)["configfile"]:
            cmd.append("-V")
            self.yam = vars(self.args)["configfile"]
            cmd.append(self.yam)
        # adding tags option
        if vars(self.args)["jira_test_suit_id"] or vars(self.args)["clone id"]:
            if tags:
                cmd.append("-i")
                cmd.append(tags)
            else:
                raise Exception("No test cases mentioned to run")
        tcname = vars(self.args)["testcasename"]
        # appending -t option with testcase names
        if tcname and not '-i' in sys.argv:
            if ',' in tcname:
                tcname = tcname.split(',')
                for tc in tcname:
                    cmd.append("-t")
                    cmd.append(tc)
            else:
                cmd.append("-t")
                cmd.append(tcname)
        if not vars(self.args)["jira_test_suit_id"]:
            labels = vars(self.args)["label"]
            if labels:
                if (',' in labels or 'OR' in labels):
                    if ',' in labels:
                        labels_list = labels.split(',')
                    if 'OR' in labels:
                        labels_list = labels.split('OR')
                    found_tcs = []
                    for tc in robottcs:
                        robottcs[tc] = [tag.lower() for tag in robottcs[tc]]
                        for label in labels_list:
                            if label.lower() in robottcs[tc]:
                                found_tcs.append(tc)
                                cmd.append("-t")
                                cmd.append(tc)
                                continue
                    if not found_tcs:
                        errormsg = "Given testsuite has no testcases which has any of {} labels".format(','.join(labels_list))
                        logger.error(errormsg)
                        raise Exception(errormsg)
                elif 'AND' in labels:
                    labels_list = labels.split('AND')
                    not_found_tcs = 0
                    for tc in robottcs:
                        robottcs[tc] = [tag.lower() for tag in robottcs[tc]]
                        count = 0
                        for label in labels_list:
                            if label.lower() in robottcs[tc]:
                                count+=1
                        if count == len(labels_list):
                            cmd.append("-t")
                            cmd.append(tc)
                        else:
                            not_found_tcs += 1
                    if not_found_tcs == len(robottcs):
                        errormsg = "Given testsuite has no testcases which contains all the {} labels".format(','.join(labels_list))
                        logger.error(errormsg)
                        raise Exception(errormsg)
                else:
                    cmd.append("-i")
                    cmd.append(labels)
        if vars(self.args)["tcsuite"]:
            # appending robot file to arguments.
            cmd.append(vars(self.args)["tcsuite"])
        # passing command arguments to run_cli method of robot framework
        logger.info(cmd)
        run_cli(cmd, exit=False)


def _findvalue_in_dict(dic, key, default=None):
    """
    Return a value corresponding to the specified key in the (possibly
    nested) dictionary dic. If there is no item with that key, return
    default.
    """
    if key in dic:
        return dic[key]
    stack = [iter(list(dic.items()))]
    while stack:
        for k, v in stack[-1]:
            if isinstance(v, dict):
                stack.append(iter(list(v.items())))
                break
            elif k == key:
                return v
        else:
            stack.pop()
    return default


def sutas(SUTAS):
    """
    Main function for testsuite execution.

    Validates robot file for testcase dependency.
    Clones testsuite and testcases if testcase management is enabled in
    global config file.
    Run testsuite using robotframework command pybot.
    Send notifications to Slack and Microsoft teams channels.

    - **parameters**, **types**, **return** and **return types**::

        param SUTAS: Sutas classs object.
        type SUTAS: class object
    """
    global subject
    try:
        # copy config yaml file to test logs directory.
        if vars(SUTAS.args)["configfile"]:
            copyfile(vars(SUTAS.args)["configfile"], os.path.join(
                output_dir, os.path.basename(vars(SUTAS.args)["configfile"])))
        # copy testsuite file(robot file) to test logs directory.
        if "-s" in sys.argv:
            copyfile(os.path.abspath(vars(SUTAS.args)["tcsuite"]), os.path.join(
                output_dir, os.path.basename(vars(SUTAS.args)["tcsuite"])))
            # get username and password of jira from user_info file
            if "Jira" in DATA:
                user_name = DATA["Jira"]["username"]
                pwd = DATA["Jira"]["password"]
                suite_details['username'] = user_name
                suite_details['pwd'] = pwd
            # get other jira details from global_config file
            if "Jira" in glob_data:
                url = glob_data["Jira"]["url"]
                proj = glob_data["Jira"]["project"]
                suite_details['url'] = url
                suite_details['proj'] = proj
            if glob_data.get('EnableDatabase','no').lower()=='yes':
                if "-l" not in sys.argv:
                    try:
                        if "-t" not in sys.argv:
                            raise TestBuildTypeException
                    except TestBuildTypeException as err:
                        mailobj = EmailNotification().emailobj()
                        body = "TestBuildType must be provided while executing Suite"
                        mailobj.send_mail_when_failed(body)
                        logger.error(body)
                        sys.exit(1)
            # establishing Jira connection
            if "-j" in sys.argv or "-i" in sys.argv:
                obj = Jiralib(url, user_name, pwd)
                conn = obj.conn
            if "-j" in sys.argv:
                test_suite_id = vars(SUTAS.args)['jira_test_suit_id']
            else:
                test_suite_id = vars(SUTAS.args)['clone id']
            if '-t' in sys.argv:
                os.environ['testnames'] = vars(SUTAS.args)["testcasename"]
            test_suite_name = vars(SUTAS.args)['tcsuite'].split("\\")[-1]
            if not test_suite_id or \
               glob_data.get('EnableTestManagement').lower() == "no":
                notify.message("*Test suite {} execution "
                               "started*\n".format(test_suite_name))
                subject = test_suite_name
            if not test_suite_id:
                suite_details['master_suite_id'] = test_suite_id
            logger.warn("Checking if tescases are in proper dependency order.")
            ValidateRobotFile(SUTAS.robo_file).validate_testdata()
            tags = None
            tc_management = None
            if suite_details.get('database').lower() == 'yes':
                ts_obj = test_suite()
            start_time = datetime.datetime.now()
            ts_name = test_suite_name
            ts_data = {'start_time': None, 'master_ts_id': None,
                       'run_id': None, 'ts_id': None, 'name': None,
                       'project_id': None,
                       'description': None, 'test_suite_type': None}
            testtype = None
            if '-l' in sys.argv:
                TBTypes = fetch_data_from_testenvdata('TestBuildTypes')
                if vars(SUTAS.args)['label'] not in TBTypes:
                    mailobj = EmailNotification().emailobj()
                    body = "TestBuildType must be specified from one of the following {}".format(TBTypes)
                    mailobj.send_mail_when_failed(body)
                    logger.error(body)
                    sys.exit(1)
                testtype = vars(SUTAS.args)['label']
                os.environ['testtype'] = testtype
                ts_data['test_suite_type'] = testtype
            if "-j" in sys.argv or '-i' in sys.argv:
                if glob_data.get('EnableTestManagement').lower() == "yes":
                    tc_management = True
                    if '-j' in sys.argv:
                        msg = ("*Clonning Master copy Test"
                               "suite {}*\n".format(test_suite_id))
                        logger.warn(msg)
                        notify.message(msg)
                cloneid = ''
                idtype = ''
                clonetype = ''
                if '-t' in sys.argv and not '-i' in sys.argv:
                    status = vars(SUTAS.args)["testcasename"].lower()
                if '-i' in sys.argv:
                    status = 'failed'
                    cloneid = vars(SUTAS.args)["clone id"].lower()
                    clonetype = conn.issue(
                        cloneid).fields.issuetype.name.lower()
                    if '-t' in sys.argv:
                        status = vars(SUTAS.args)["testcasename"].lower()

                        if clonetype not in ['testsuite', 'test suite']:
                            msg = ('Please provide clone test suite id '
                                   'instead of test case id-{}'.format(
                                       cloneid))
                            raise Exception(msg)
                    if clonetype in ['testsuite', 'test suite']:
                        # clonning testsuite in Jira
                        tags, clonedts_issue_obj = TestManagement.get_test_case_tags(conn,
                                                                            test_suite_id,
                                                                            rerun=True,
                                                                            type=status
                                                                            )
                        # attaching testsuite file(robot file) and
                        # config.yaml file to cloned testsuite
                        conn.add_attachment(issue=clonedts_issue_obj,
                                            attachment=vars(SUTAS.args)["tcsuite"])
                        if vars(SUTAS.args)["configfile"]:
                            conn.add_attachment(
                                issue=clonedts_issue_obj, attachment=vars(SUTAS.args)["configfile"])
                    else:
                        msg = ('Rerunning single failed '
                               'test case:- {}'.format(
                                   cloneid.upper()))
                        logger.warn(msg)
                        fieldmap = {field['name']: field['id']
                                    for field in conn.fields()}
                        sutas_id_field = fieldmap['sutas_id']
                        tags, clonedts_issue_obj = conn.issue(cloneid).raw['fields'][
                            sutas_id_field], conn.issue(cloneid)
                        tc_data = {}
                        tc_data[tags] = (
                            clonedts_issue_obj.key, clonedts_issue_obj.fields().summary)
                        os.environ.__dict__["testids"] = tc_data
                        make_transitions(conn, clonedts_issue_obj)
                else:
                    cloneid = vars(SUTAS.args)["jira_test_suit_id"]
                    if ',' in cloneid:
                        jiraids = cloneid.split(',')
                        for jiraid in jiraids:
                            idtype = conn.issue(
                                jiraid).fields.issuetype.name.lower()
                            if idtype in ['test suite', 'testsuite']:
                                continue
                            else:
                                msg = 'Provided jira id {} is not a master suites and check other ids also'.format(
                                    jiraid)
                                raise Exception(msg)
                    else:
                        idtype = conn.issue(cloneid).fields.issuetype.name
                    if idtype.lower() in ['testsuite', 'test suite']:
                        tags, clonedts_issue_obj = TestManagement.get_test_case_tags(conn,
                                                                            test_suite_id, testtype)
                        conn.add_attachment(
                            issue=clonedts_issue_obj, attachment=vars(SUTAS.args)["tcsuite"])
                        if vars(SUTAS.args)["configfile"]:
                            conn.add_attachment(
                                issue=clonedts_issue_obj, attachment=vars(SUTAS.args)["configfile"])
                    else:
                        logger.error("\033[32m Provided testcase id {}".format(cloneid))
                        raise Exception('Please mention Master Test Suite id')
                if suite_details.get('database').lower() == 'yes':
                    if (cloneid and clonetype in ['testsuite', 'test suite']):
                        master_suite_id = clonedts_issue_obj.raw['fields'][
                            'issuelinks'][0]['outwardIssue']['key']
                    else:
                        if not clonetype in ['testcase', 'test case']:
                            master_suite_id = test_suite_id
                        else:
                            test_suite_id = clonedts_issue_obj.fields.parent.key
                            iss = conn.issue(test_suite_id)
                            master_suite_id = iss.raw['fields'][
                                'issuelinks'][0]['outwardIssue']['key']
                    # collecting testsuite data to be stored in database
                    ts_data = {'start_time': start_time,
                               'master_ts_id': master_suite_id,
                               'run_id': suite_details.get('run_id'), }

                if clonedts_issue_obj.key == test_suite_id:
                    test_suite_id = clonedts_issue_obj.key
                else:
                    if (clonetype in ['testsuite', 'test suite'] or idtype.lower() in ['testsuite', 'test suite']):
                        test_suite_id = clonedts_issue_obj.key
                    else:
                        clonedts_issue_obj = conn.issue(test_suite_id)

                ts_name = clonedts_issue_obj.fields().summary
                ts_description = clonedts_issue_obj.fields().description
                project_id = clonedts_issue_obj.key.split('-')[0]
                proj_name = Jiralib.find_project_by_key(conn,
                                                        project_id)
                fieldmap = {field['name']: field['id'] for field in conn.fields()}
                sprint_field = fieldmap.get('Sprint')
                sprint_data = conn.issue(clonedts_issue_obj).raw['fields'].get(sprint_field)
                sprint_name = None
                if sprint_data:
                    sprint_data = sprint_data[0].split(',')
                    for dat in sprint_data:
                        if 'name' in dat:
                            sprint_name = dat.split('=')[1]
                suite_details['sprint_number'] = sprint_name
                # collecting few more details to push it to database
                if suite_details.get('database').lower() == 'yes':
                    db_util_obj = Db_utils()
                    if not db_util_obj.get_rows_by_name(projects,
                                                        proj_name):
                        proj_obj = projects()
                        proj_data = {'name': proj_name,
                                     'project_id': project_id}
                        proj_id = db_util_obj.write(proj_obj, proj_data)
                    else:
                        proj_id = db_util_obj.get_id_by_name(projects,
                                                             proj_name)
                    ts_data.update({'ts_id': test_suite_id,
                                    'name': ts_name, 'project_id': proj_id,
                                    'description': ts_description, 'test_suite_type': testtype})
                    user_id = conn.myself().get('key')
                    users_db_id = db_util_obj.chk_user_id(users, user_id)
                    user_obj = conn.user(user_id)
                    slack_id = _findvalue_in_dict(glob_data, 'channelname')
                    teams_url = _findvalue_in_dict(glob_data, 'Teams')
                    if teams_url:
                        teams_url = teams_url.get('url')
                    usr_data = {'jira_id': user_obj.name, 'email_id': user_obj.emailAddress,
                                'project_id': proj_id, 'slack_id': slack_id,
                                'teams_url': teams_url, }
                    if not users_db_id:
                        userobj = users()
                        usr_data.update(
                            {'user_id': user_id, 'name': user_obj.displayName, })
                        db_util_obj.write(userobj, usr_data)
                    else:
                        db_util_obj.update_data_bulk(
                            users, users_db_id, usr_data)
                if glob_data.get('EnableTestManagement').lower() == "yes":
                    notify.message("*Clonned Test suite {} execution "
                                   "started*\n".format(test_suite_id))
                    subject = ("Test results of clonned test "
                               "suite {}".format(test_suite_id))
                if suite_details.get('database').lower() == 'yes':
                    db_util_obj = Db_utils()
                    ts_db_id = db_util_obj.write(ts_obj, ts_data)
                    suite_details.update({'ts_db_id': ts_db_id})
            else:
                ts_data['start_time'] = start_time
                ts_data['name'] = ts_name
                project_id = glob_data.get('TM_Project')
                if suite_details.get('database').lower() == 'yes':
                    db_util_obj = Db_utils()
                    proj_name = db_util_obj.get_project_name_by_id(projects,project_id)
                    fix_version_name = glob_data.get('fix_version')
                    if not db_util_obj.get_rows_by_name(projects,proj_name):
                        proj_obj = projects()
                        proj_data = {'name': proj_name,'project_id': project_id}
                        proj_id = db_util_obj.write(proj_obj, proj_data)
                    else:
                        proj_id = db_util_obj.get_id_by_name(projects,proj_name)
                    fix_version_db_id = db_util_obj.chk_fix_version(fix_version, fix_version_name)
                    ts_data['project_id'] = proj_id
                    ts_db_id = db_util_obj.write(ts_obj, ts_data)
                    suite_details.update({'ts_db_id': ts_db_id})
                    suite_details['sprint_number'] = glob_data.get('sprint_number')
                    suite_details['fix_version_db_id'] = fix_version_db_id

            raise_bugs = glob_data.get("Raise_Bugs").lower()

            suite_details.update({'ts_id': test_suite_id})
            suite_details['robo_file'] = SUTAS.robo_file
            suite_details['affects_version'] = \
                glob_data.get('Jira').get('affects_version')
            if glob_data.get('environment'):
                suite_details['environment'] = glob_data.get('environment')
            suite_details['watcher'] = glob_data.get('Jira').get('watcher')
            suite_details['bugpriority'] = glob_data.get('Jira').get('bugpriority')
            suite_details['bugseverity'] = glob_data.get('Jira').get('bugseverity')
            suite_details['tc_management'] = tc_management
            suite_details['outputdir'] = output_dir
            suite_details['Raise_Bugs'] = raise_bugs
            suite_details['EnableTestManagement'] = \
                glob_data.get('EnableTestManagement').lower()
            os.environ.__dict__["context"] = {}
            os.environ.__dict__["context"].update(suite_details)
            if raise_bugs.lower() == 'no':
                msg = ("Raise_Bugs is set to 'no' in config file, "
                       "hence not raising any bugs.")
                logger.warn(msg, console=False)
                notify.message(msg)
            # storing config yaml file path in environ variable
            SUTAS.save_config_path()
            # Running testsuite
            SUTAS.run_test_suite(tags)
            ParseAndRaiseBug.chk_stats(output_dir)
            if suite_details.get('database').lower() == 'yes' and ts_obj and ts_data:
                db_util_obj = Db_utils()
                end_time = datetime.datetime.now()
                ts_data = {'end_time': end_time, 'status': 'completed'}
                db_util_obj.update_data_bulk(test_suite, ts_db_id, ts_data)
            # Calculating and comparing the performance of testsuite, testcase
            # and keywords.
            if vars(SUTAS.args)["benchmark"]:
                perfcompare(os.path.join(output_dir, 'output.xml'), os.path.abspath(
                    vars(SUTAS.args)['benchmark']), output_dir)
                # Pushing performance output text file to test artifacts server
                TestArtifact(os.path.join(output_dir,
                                          "perf.txt")).push_artifacts()
            # Pushing output.xml, log.html and report.html to artifactory.
            TestArtifact(os.path.join(output_dir,
                                      "output.xml")).push_artifacts()
            TestArtifact(os.path.join(output_dir, "log.html")).push_artifacts()
            TestArtifact(os.path.join(output_dir,
                                      "report.html")).push_artifacts()

            robo_file = os.path.basename(vars(SUTAS.args)["tcsuite"])
            path_to_robo_file = os.path.join(output_dir, robo_file)
            # pushing testsuite file(robot file) to test artifact server
            TestArtifact(path_to_robo_file).push_artifacts()
            if vars(SUTAS.args)["configfile"]:
                config_file = os.path.basename(vars(SUTAS.args)["configfile"])
                path_to_config_file = os.path.join(output_dir, config_file)
                # pushing config file to artifactory
                TestArtifact(path_to_config_file).push_artifacts()

        else:
            help(sys.argv)
    except DependencyException as e:
        logger.error(e)
        out = "\n" + traceback.format_exc()
        logger.warn(out)
        sys.exit()
    except IncorrectRobotfile as e:
        logger.error(e)
        out = "\n" + traceback.format_exc()
        logger.warn(out)
        sys.exit()
    except Exception as e:
        logger.error(e)
        out = "\n" + traceback.format_exc()
        logger.warn(out)

        if not "user_setup" in sys.argv:
            logger.warn("Test execution Failed.")
            notify.message("Test execution Failed")
            notify.message(str(e))
    finally:
        # sending consolidated message to slack, MS teams and email.
        if "-e" in sys.argv:
            os.environ['envandteninfo'] = vars(SUTAS.args)["environment"]
        if "-s" in sys.argv:
            notify.send_message()
            if 'Consolidatedmail' in glob_data:
                if glob_data['Consolidatedmail'].lower() == 'no':
                    notify.send_mail(subject)
                if glob_data['Consolidatedmail'].lower() == 'yes':
                    consolidated_report = os.path.join(os.path.dirname(output_dir),
                                                       "Consolidated_report.html")
                    consolidated_log = os.path.join(os.path.dirname(output_dir),
                                                    "Consolidated_log.html")
                    if os.path.exists(consolidated_report) and os.path.exists(consolidated_log):
                        TestArtifact(consolidated_log).push_artifacts()
                        TestArtifact(consolidated_report).push_artifacts()
        if "-j" in sys.argv and glob_data['EnableTestManagement'].lower() == "yes":
            try:
                transitions = conn.transitions(test_suite_id)
                for transition in transitions:
                    if transition['name'].lower() in ['done', 'completed']:
                        conn.transition_issue(
                            test_suite_id, str(transition['id']))
            except UnboundLocalError:
                pass
            except JIRAError as e:
                logger.warn(e.status_code)
                logger.warn(e.text)


def run(args, parallel=False):
    """
    Entry point for testsuite execution.

    Validates global and user config files. Calls sutas function to start
    testsuite execution.

    - **parameters**, **types**, **return** and **return types**::

    param args: List of sutas command. sutas command split with space.
    type args: list

    """
    sys.argv = []
    sys.argv = args
    global suite_details
    global output_dir
    global DATA
    global glob_data
    global globalfilepath

    SUTAS = Sutas(sys.argv[1:])
    filepath = os.path.join(expanduser('~'), "user_info.yaml")
    globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
    DATA = get_data_from_yaml(filepath)
    glob_data = get_data_from_yaml(globalfilepath)
    output_dir = create_log_file(sys.argv)
    os.environ['output_dir'] = output_dir
    msg = "Validating user_info file."
    logger.warn(msg)
    notify.message(msg)
    # Validating Jira, database and communication channels data provided
    # by user
    userobj = ValidateUserConfig()
    userobj.validate_env()
    userobj.validate_jira()
    userobj.validate_database()
    userobj.validate_communication_channels()

    msg = "Validation of user_info file is Successful."
    # displays what all configurations are enabled.
    SUTAS.show_config()
    # displays on console if execution is Parallel.
    if parallel:
        notify.message("Parallel Execution is True")
    if glob_data and glob_data.get('EnableTestManagement').lower() == 'yes':
        if glob_data.get('Raise_Bugs').lower() == 'no':
            logger.warn("Jira TestManagement is enabled but Bug management is disabled.")

    if glob_data and glob_data.get('EnableDatabase'):
        suite_details.update({'database': glob_data.get('EnableDatabase')})
    try:
        run_id = None
        if "-j" in sys.argv:
            if glob_data.get('EnableTestManagement','no').lower() == 'yes':
                suite_details.update({'jira': 'yes'})
            else:
                raise Exception('TestManagement must be enabled if master suite id  with "-j" is specified')
        if suite_details.get('database').lower() == 'yes':
            global db_util_obj
            db_util_obj = Db_utils()
            # checks the diskspace on DB server. If it reaches threshold value
            # then it will start pruning.
            if glob_data['Database']['prune'].lower() == 'yes':
                db_util_obj.check_diskspace()
                if db_util_obj.lock():
                    logger.warn('pruning the database..')
                    if db_util_obj.delete_data(test_case):
                        if db_util_obj.delete_data(test_suite):
                            db_util_obj.delete_data(test_execution)
                            logger.warn('Database pruning completed')
                            db_util_obj.unlock()
            te_obj = test_execution()
            start_time = datetime.datetime.now()
            os_type = platform.platform()
            hostname = socket.gethostname()
            host_ip = socket.gethostbyname(hostname)
            # Gathering start_time, os_type, hostname and host ip information
            # to update in the database.
            te_data = {'start_time': start_time, 'os_type': os_type,
                       'hostname': hostname, 'host_ip': host_ip}

            run_id = db_util_obj.write(te_obj, te_data)
            suite_details.update({'run_id': run_id})
        sutas(SUTAS)
        if suite_details.get('database').lower() == 'yes':
            # Gathering end time, process id, memory utilization, cpu time to
            # update in to database.
            end_time = datetime.datetime.now()
            pid = os.getpid()
            p_in = psutil.Process(pid)
            mem = p_in.memory_info().rss
            mem = round((float(mem) / (1024 * 1024)), 2)
            cpu_time = p_in.cpu_times()
            cpu_time = round((cpu_time.user + cpu_time.system), 2)
            te_data.update({'end_time': end_time,
                            'cpu_time': cpu_time, 'memory_usage': mem, })
    finally:
        if suite_details.get('database').lower() == 'yes':
            # Storing gathered data in to database.
            if run_id:
                db_util_obj = Db_utils()
                db_util_obj.update_data_bulk(test_execution, run_id, te_data)


def run_parallel(argv):
    '''
    Run testsuites in parallel.

    From list of commands each command is run as different process using
    Process method from multiprocessing.

    - **parameters**, **types**, **return** and **return types**::

        param argv: List of sutas commands to be run
        type argv: list
    '''
    process = []
    # iterating through list of lists of sutas commands.
    for cmdargs in argv:
        # creating one process per each sutas command.
        process.append(
            Process(target=run, args=(cmdargs, dict(parallel=True))))
    # starting all the above created processes and joining them.
    for i in process:
        i.start()
    for i in process:
        i.join()


def run_sequential(argv):
    '''
    Run testsuites in sequential order.

    From list of commands each command is passed to run fucntion.

    - **parameters**, **types**, **return** and **return types**::

        param argv: List of sutas commands to be run
        type argv: list
    '''
    maxtime = None
    firstexecution = True
    # iterating through list of lists of sutas commmands and checking if
    # each command has -d mentioned in it or not. If mentioned then checking
    # if -c is mentioned. If yes then it will start the count and run. Else it
    for cmdargs in argv:
        # checking if -d is mentioned or not.
        if "-d" in cmdargs:
            # checking if c(count) is mentioned or not. If mentioned then it will
            # start the count and execute that many times.
            if "c" in cmdargs[cmdargs.index("-d") + 1].lower():
                count = int(cmdargs[cmdargs.index("-d") + 1][:-1])
                while count > 0:
                    run(cmdargs)
                    count = count - 1
            # if c(count) not mentioned then it will go for M which is minutes
            # it will run the test suite for that many minutes.
            else:
                stoptime = cmdargs[cmdargs.index("-d") + 1][:-1]
                os.environ["stoptime"] = str(time.time() + 60 * int(stoptime))
                while float(os.environ["stoptime"]) > time.time():
                    starttime = time.time()
                    run(cmdargs)
                    endtime = time.time()
                    timetaken = endtime - starttime
                    if maxtime:
                        if timetaken > maxtime:
                            maxtime = timetaken
                    else:
                        maxtime = timetaken
                    # if it is not first iteration, it checks the stoptime and
                    # current time so that it can stop execution if stoptime is
                    # already reached. then notifies user with below message.
                    if not firstexecution:
                        if float(os.environ["stoptime"]) <= time.time():
                            notify.message("*Last iteration took more than "
                                           "previous iterations.*")
                        lefttime = float(os.environ["stoptime"]) - time.time()
                        # Compares lefttime and maxtime to notify user whether
                        # it is starting next iteration or not.
                        if lefttime < maxtime:
                            notify.message("*Time left is less than the max "
                                           "execution time hence not "
                                           "starting next iteration.*")
                            break
                    # if it is first iteration then it checks the stoptime and
                    # current time so that it can stop execution if stoptime is
                    # already  reached. Notifies user with appropriate messge.
                    else:
                        firstexecution = False
                        if float(os.environ["stoptime"]) <= time.time():
                            notify.message("*First iteration itself took "
                                           "more than specified duration*")

                notify.send_message()
                del os.environ["stoptime"]
        # if it is normal execution without duration then it calls run method
        # directly.
        else:
            run(cmdargs)


def main():
    '''
    This function parses provided argfile and forms sutas commands.

    Parses argfile which contains testsuite robot file, config file
    and Jira id in each line.
    From each line of argfile one sutas command is formed which is appended to
    another list.
    This list of sutas commands are passed to run_sequential fucntion if -p
    option is not passed. If -p is passed then the list of commands will be
    passed to run_parallel function.
    '''
    cmd = "sutas " + " ".join(sys.argv[1:])
    os.environ['cmd'] = 'Triggered command "{}"'.format(cmd)
    if not 'user_setup' in sys.argv:
        cmd = 'Triggered command "{}"'.format(cmd)
        logger.info(cmd)
        notify.message(cmd)
    global output_dir
    global subject
    os.environ['argfileresult'] = '0,0,0'
    if 'user_setup' in sys.argv and len(sys.argv) > 2:
        msg = "*Triggered 'sutas user_setup' command with options"
        hash = "#" * len(msg)
        msg = hash + "\n" + msg + "\n" + hash + "\n"
        cmd = 'Triggered command "{}"'.format(cmd)
        logger.info(cmd)
        notify.message(msg)
    else:
        msg = "*Triggered '%s'*" % (" ".join(sys.argv))
        hash = "#" * len(msg)
        msg = hash + "\n" + msg + "\n" + hash + "\n"
        notify.message(msg)
    sutasfolder = os.path.join(os.path.expanduser('~'), "Sutas_Logs")
    suitelogpaths = os.path.join(sutasfolder, "suitelogpaths")
    if os.path.isfile(suitelogpaths):
        os.remove(suitelogpaths)
    SUTAS = Sutas(sys.argv)
    SUTAS.validate_args()
    filepath = os.path.join(expanduser('~'), "user_info.yaml")
    globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
    DATA = get_data_from_yaml(filepath)
    glob_data = get_data_from_yaml(globalfilepath)
    
    # creates 'sutas_usersetup<timestamp>.log' file if user_setup in sys.argv
    if "user_setup" in sys.argv:
        output_dir = create_log_file(sys.argv)
    # if argfile is provided, it will validate and parse argfile
    if vars(SUTAS.args)['argfile']:
        testsfile = vars(SUTAS.args)['argfile']
        # validateandparseargfile will return errormsg if any in argfile and
        # argv which contains list of lists of sutas commands.
        errormsg, argv = validateandparseargfile(testsfile)
        if errormsg:
            notify.send_message()
            raise Exception(errormsg)
        if not all([os.path.isfile(args[args.index('-s')+1]) for args in argv if '-s' in args]):
            logger.info(argv)
            raise Exception("Check the test suites in argfile and provide the valid argfile")
        if not all([os.path.isfile(os.path.abspath(args[args.index('-c')+1])) for args in argv if '-c' in args]):
            logger.info(argv)
            raise Exception("Check the testdata yaml files in argfile and provide the valid argfile")
        if glob_data.get('EnableTestManagement').lower() == "yes":
            if "Jira" in DATA:
                user_name = DATA["Jira"]["username"]
                pwd = DATA["Jira"]["password"]
            if "Jira" in glob_data:
                url = glob_data["Jira"]["url"]
                obj = Jiralib(url, user_name, pwd)
                conn = obj.conn
                jira_issues = [args[args.index('-j')+1] for args in argv if '-j' in args]
                for jira_issue in jira_issues:
                    jira_issue_list = jira_issue.split(',')
                    [conn.issue(issue) for issue in jira_issue_list]
        # if parallel in args then it will call run_parallel method else
        # it will call run_sequential
        if vars(SUTAS.args)['parallel'].lower() == "true":
            run_parallel(argv)
        else:
            run_sequential(argv)
    # if tcsuite is provided instead of argfile then it will directly call
    # run_sequential method.
    elif vars(SUTAS.args)['tcsuite']:
        os.environ['argfile'] = ''
        run_sequential([sys.argv])
    # if Consolidatemail is Yes in config file then sutas will send
    # consolidated mail.
    if "Consolidatedmail" in glob_data:
        if glob_data['Consolidatedmail'].lower() == 'yes':
            if os.environ['argfile']:
                subject = os.path.basename(os.environ['argfile']).split('.')[0]
            if vars(SUTAS.args)["environment"]:
                os.environ['envandteninfo'] = vars(SUTAS.args)["environment"]
            notify.send_mail(subject)
            consolidated_report = os.environ['consolidated_report']
            consolidated_log = os.environ['consolidated_log']
            if os.path.exists(consolidated_report) and os.path.exists(consolidated_log):
                TestArtifact(consolidated_log).push_artifacts()
                TestArtifact(consolidated_report).push_artifacts()

    try:
        testsuiteresult = os.environ['suiteresult']
        passed, skipped, failed = [int(val) for val in re.findall(r'\d{1,3}', testsuiteresult)]
    except KeyError as ValueError:
        passed, skipped, failed = [0, 0, 0]
    try:
        pass_percentage = passed*100/(passed+skipped+failed)
    except ZeroDivisionError:
        logger.warn('STATUS: FAILURE')
        sys.exit(1)    
    
    if '-l' in sys.argv:            
        TestType = sys.argv[sys.argv.index('-l')+1]
        data = fetch_data_from_testenvdata('Threshold_Buildtype_Mapping')
        logger.warn("Defined Thresholds for all TestBuildTypes are {}".format(data))
        if TestType in list(data.keys()):
            if pass_percentage >= data[TestType]:
                status, return_value, limit = 'SUCCESS', 0, 'above/equalto'
            else:
                status, return_value, limit = 'FAILURE', 1, 'below'
            logger.warn('Pass_Percentage of "{}/s" Executed is {} which is {} Threshold value {}'.
                        format(TestType,pass_percentage,limit,data[TestType]))
            logger.warn('STATUS: {}'.format(status))
            sys.exit(return_value)
    else:
        if int(skipped) == 0 and int(failed) == 0 and int(passed) != 0:
            logger.warn('STATUS: SUCCESS')
            sys.exit(0)
        else:
            logger.warn('STATUS: FAILURE')
            sys.exit(1)    

if __name__ == "__main__":
    main()
