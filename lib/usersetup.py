"""
This module is for setting up user_info.yaml file.
"""
import getpass
import os
import re
import sys
from tabulate import tabulate
from os.path import expanduser
from lib import logger
from lib.AESCipher import AESCipher
from lib.IntConfig import notify
from lib.ValidateUserConfig import ValidateUserConfig
from lib.TestArtifact import TestArtifact
from lib.utilities import (create_log_file, dump_data_into_yaml,
                           get_data_from_yaml)
import yaml


class UserSetup(object):
    """
    This class implements the user info setup.
    """

    def __init__(self):
        """
            Gets the data from user_info and global_conf file yaml files
        """
        self.filepath = os.path.join(expanduser('~'), "user_info.yaml")
        self.globalfilepath = os.path.join(expanduser('~'),
                                           "global_conf.yaml")
        create_log_file(sys.argv)
        self.userprevdata = self.userdata()
        self.globalprevdata = self.globaldata()
        self.user_setup()

    def globaldata(self):
        '''
        Loads the previous data from global_conf.yaml.

        - **parameters**, **types**, **return** and **return types**::
            return: globalprevdata on success else empty dict
            rtype: dictionary
        '''
        if os.path.exists(self.globalfilepath):
            with open(self.globalfilepath, 'r') as globalfile:
                globalprevdata = yaml.load(globalfile, Loader=yaml.FullLoader)
                return globalprevdata
            if not globalprevdata:
                globalprevdata = {}
                return globalprevdata
        else:
            print("no global configuration file found to load previous data.")
            return {}

    def userdata(self):
        '''
        Loads the previous data from user_info.yaml.

        - **parameters**, **types**, **return** and **return types**::
            return: userprevdata on success else empty dict
            rtype: dictionary
        '''
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as userfile:
                userprevdata = yaml.load(userfile, Loader=yaml.FullLoader)
                return userprevdata
            if not userprevdata:
                userprevdata = {}
                return userprevdata
        else:
            print("no global configuration file found to load previous data.")
            return {}

    def prevdata(self, key, prevdata):
        '''
        Parse the previous data by using key in global_conf.yaml.

        - **parameters**, **types**, **return** and **return types**::

          :param key: key to be find in a dictionary
          :paramprevdata: yaml data from global_conf.yaml or user_info.yaml
          :type key: String
          :type prevdata: dictionary
          :return: Returns data of dictionary key
          :rtype: string
        '''
        keys = key.split(".")
        try:
            if len(keys) > 1:
                data = prevdata[keys[0]][keys[1]]
            else:
                data = prevdata[keys[0]]
        except KeyError:
            if len(keys) > 1:
                prevdata.update({keys[0]: {keys[1]: ""}})
            else:
                prevdata[keys[0]] = ""
        finally:
            if len(keys) > 1:
                return prevdata[keys[0]][keys[1]]
            else:
                return prevdata[keys[0]]

    def add_mailconf(self):
        """
        Add mail details into YAML.

        - **parameters**, **types**, **return** and **return types**::

          :return: Returns email dictionary
          :rtype: dictionary

        """
        emailnotifications = ("\nDo you want notifications to Email["
                              + self.prevdata('EmailNotifications',
                                              self.globalprevdata) +
                              "]:(Yes/No)")
        emailnotifications = self.get_input(emailnotifications, choices=["yes",
                                                                         "no"])
        email_if_failed = ("\nDo you want Email notifications only if testcases failed["
                           + self.prevdata('send_mail_only_if_failed',
                                           self.globalprevdata) +
                           "]:(Yes/No)")
        email_if_failed = self.get_input(email_if_failed, choices=["yes","no"])
        
        emails = self.prevdata('Email.recipients', self.globalprevdata)
        consolidatedmail = self.prevdata('Consolidatedmail',
                                         self.globalprevdata)
        smtpip = self.prevdata('Email.smtpip', self.globalprevdata)
        smtpport = self.prevdata('Email.smtpport', self.globalprevdata)
        validateemails = self.prevdata('Email.ValidateEmails', self.globalprevdata)
                
        if emailnotifications.lower() == 'yes':
            smtpip = ("Enter SMTP server IP [" + smtpip + "]:")
            smtpip = self.get_input(smtpip)
            smtpport = ("Enter SMTP port ["
                        + str(smtpport) + "]:")
            smtpport = self.get_input(smtpport)
            if smtpport.isdigit():
                smtpport = int(smtpport)
            pattern = r"(^[a-z][a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.com$)"
            for i in range(5):
                flag = False
                emails = "\nEnter recipient email-ids seperated by comma [" +\
                    emails + "]: "
                emails = self.get_input(emails)
                valemails = emails.split(",")
                for email in valemails:
                    if not re.findall(pattern, email):
                        logger.warn(
                            "\nemail %s is not in correct format." % email)
                        flag = True
                if not flag:
                    break
            consolidatedmail = "Do you want Consolidated Email[" +\
                consolidatedmail + "]:(Yes/No)"
            consolidatedmail = self.get_input(consolidatedmail,
                                              choices=["yes", "no"])
            validateemails = ("\nDo you want validate emails(A validation email sent to all recipients by SUTAS.)["
                                  + self.prevdata('Email.ValidateEmails',
                                                      self.globalprevdata) +
                                      "]:(Yes/No)")
            validateemails = self.get_input(validateemails, choices=["yes",
                                                                         "no"])            
        email_dict = {'EmailNotifications': emailnotifications,
                      'Email': {'recipients': emails,
                                'smtpip': smtpip,
                                'smtpport': smtpport,
                                'ValidateEmails': validateemails},
                      'Consolidatedmail': consolidatedmail,
                      'send_mail_only_if_failed': email_if_failed
                      }
        return email_dict

    def add_teamsconf(self):
        """
        Add slack details into YAML.

        - **parameters**, **types**, **return** and **return types**::

          :return: Returns slack dictionary
          :rtype: dictionary

        """
        teamsnotifications = ("\nDo you want notifications to "
                              "Microsoft teams ["
                              + self.prevdata('TeamsNotifications',
                                              self.globalprevdata) +
                              "]:(Yes/No)")
        teamsnotifications = self.get_input(teamsnotifications, choices=["yes",
                                                                         "no"])
        url = self.prevdata('Teams.url', self.globalprevdata)
        if teamsnotifications.lower() == 'yes':
            url = "Enter microsoft teams channel url [" + url + "]: "
            url = self.get_input(url)
        globalteams_dict = {'TeamsNotifications': teamsnotifications,
                            'Teams': {'url': url}}
        return globalteams_dict

    def add_slackconf(self):
        """
        Add slack details into YAML.

        - **parameters**, **types**, **return** and **return types**::

          :return: Returns slack dictionary
          :rtype: dictionary

        """
        slacknotifications = ("\nDo you want notifications to "
                              "Slack Channel ["
                              + self.prevdata('SlackNotifications',
                                              self.globalprevdata) +
                              "]:(Yes/No)")
        slacknotifications = self.get_input(slacknotifications, choices=["yes",
                                                                         "no"])
        usrname = self.prevdata('Slack.username', self.userprevdata)
        channelname = self.prevdata('Slack.channelname', self.globalprevdata)
        token = self.prevdata('Slack.token', self.userprevdata)
        prevtoken = token
        if token:
            token = AESCipher().decrypt(token)
            prevtoken = token
        if slacknotifications.lower() == 'yes':
            if token:
                token = AESCipher().decrypt(token)
                prevtoken = token
            usrname = "Enter username[" + usrname + "]:"
            usrname = self.get_input(usrname)
            channelname = "Enter slack channelname [" + channelname + "]: "
            channelname = self.get_input(channelname)
            while True:
                token = "enter Slack token[" + prevtoken + "]: "
                token = self.get_input(token)
                if token:
                    token = AESCipher().encrypt(token)
                    break
                else:
                    logger.warn("token cannot be empty. Please re-enter.")
        else:
            token = token
        slack_dict = {'Slack': {'username': usrname, 'token': token}}
        globalslack_dict = {'SlackNotifications': slacknotifications,
                            'Slack': {'channelname': channelname}}
        return slack_dict, globalslack_dict

    def add_artifactserverdetails(self):
        """
        Add test artifact server details into YAML.

        - **parameters**, **types**, **return** and **return types**::

          :return: Returns input values as dictionary
          :rtype: dictionary

        """
        enable_testartifact = "\nDo you want to push logs to TestArtifact server [" +\
            self.prevdata('EnableTestArtifacts',
                          self.globalprevdata) + "]:(Yes/No)"
        enable_testartifact = self.get_input(
            enable_testartifact, choices=["yes", "no"])
        serverip = self.prevdata('TestArtifact.serverip', self.globalprevdata)
        username = self.prevdata('TestArtifact.username', self.userprevdata)
        password = self.prevdata('TestArtifact.password', self.userprevdata)

        if enable_testartifact.lower() == "yes":
            serverip = ("\nFor pushing logs in to artifact server enter "
                        "apache server IP [" + serverip + "]: ")
            serverip = self.get_input(serverip)
            username = "Enter apache server username[" + username + "]: "
            username = self.get_input(username)
            password = self.get_password(
                "Enter apache server password:", password)

        artifact_dict = {'TestArtifact': {'username': username,
                                          'password': password}
                         }
        globalartifact_dict = {'TestArtifact': {'serverip': serverip},
                               'EnableTestArtifacts': enable_testartifact
                               }
        return artifact_dict, globalartifact_dict

    def add_dbconf(self):
        """
        Add slack details into YAML.

        - **parameters**, **types**, **return** and **return types**::

          :return: Returns slack dictionary
          :rtype: dictionary

        """
        enable_db = "\nDo you want to enable database [" +\
            self.prevdata('EnableDatabase', self.globalprevdata) + "]:(Yes/No)"
        enable_db = self.get_input(enable_db, choices=["yes", "no"])

        usrname = self.prevdata('Database.username', self.userprevdata)
        pwd = self.prevdata('Database.pwd', self.userprevdata)
        database_name = self.prevdata('Database.database_name',
                                      self.globalprevdata)
        prune = self.prevdata('Database.prune',
                              self.globalprevdata)
        serverip = self.prevdata('Database.serverip', self.globalprevdata)
        serverusername = self.prevdata('Database.serverusername',
                                       self.userprevdata)
        serverpwd = self.prevdata('Database.serverpassword', self.userprevdata)
        serverostype = self.prevdata(
            'Database.serverOStype', self.globalprevdata)
        if enable_db.lower() == 'yes':
            serverip = ("Enter DB Server IP["
                        + serverip + "]:")
            serverip = self.get_input(serverip)
            usrname = ("Enter database username["
                       + usrname + "]:")
            usrname = self.get_input(usrname)
            pwd = self.get_password("Enter DB password:", pwd)
            database_name = ("Enter database name[" + database_name + "]:")
            database_name = self.get_input(database_name)
            prune = "Do you want to prune the database(yes/no):[" + prune + "]"
            prune = self.get_input(prune)
            if prune.lower() == 'yes':
                serverostype = ("\nProvide os_type of machine on which db server is installed "
                                "\nEnter ostype(windows/linux) ["
                                + self.prevdata('Database.serverOStype',
                                                self.globalprevdata) + "]:")
                serverostype = self.get_input(serverostype)
                serverusername = ("\nProvde a USER CREDENTIALS who has access to "
                                  "SSH to machine. For pruning database."
                                  "\nEnter username ["
                                  + serverusername + "]:")
                serverusername = self.get_input(serverusername)
                serverpwd = self.get_password(
                    "Enter user password: ", serverpwd)

            #prune = "Do you want to prune the database:["+prune+"]"
            #prune = self.get_input(prune)

        db_dict = {'Database': {'serverusername': serverusername,
                                'serverpassword': serverpwd,
                                'username': usrname,
                                'pwd': pwd}}
        globaldb_dict = {'EnableDatabase': enable_db,
                         'Database': {'database_name': database_name,
                                      'serverip': serverip,
                                      'prune': prune,
                                      'serverOStype': serverostype}}
        return db_dict, globaldb_dict

    def update_dict(self, filename, new_dict):
        if os.path.exists(filename):
            old_dict = get_data_from_yaml(filename)
            yamldict = old_dict.copy()
            yamldict.update(new_dict)
        else:
            yamldict = new_dict
        dump_data_into_yaml(filename, yamldict, mode="w")

    def get_input(self, strng, choices=None):
        if re.search(r'\[(.*?)\]', strng):
            old_value = re.search(r'\[(.*?)\]', strng).group(1)
        else:
            old_value = ""
        while True:
            inpt = input(strng)
            if inpt == "":
                inpt = old_value
                if choices:
                    if inpt.lower() not in choices:
                        raise Exception("input must be given from the choices {}".format(choices))
                return inpt
            if choices:
                if inpt.lower() in choices:
                    break
                else:
                    logger.warn("values must be '%s' please re-enter "
                                "the value." % ("/".join(choices)))
            else:
                break
        return inpt

    def get_password(self, strng, prevpass):
        while True:
            pwd = getpass.getpass(strng)
            if pwd:
                password = AESCipher().encrypt(pwd)
                break
            else:
                if prevpass:
                    password = prevpass
                    break
                else:
                    logger.warn("No password in global conf to use."
                                "Please enter password.")
        return password

    def user_setup(self):
        """
        Gets the user config details
        """
        username = self.prevdata('Jira.username', self.userprevdata)
        password = self.prevdata('Jira.password', self.userprevdata)
        jira_url = self.prevdata('Jira.url', self.globalprevdata)
        jira_proj = self.prevdata('Jira.project', self.globalprevdata)
        raise_bugs = self.prevdata('Raise_Bugs', self.globalprevdata)
        jirabugpriority = self.prevdata(
            'Jira.bugpriority', self.globalprevdata)
        jirabugseverity = self.prevdata(
            'Jira.bugseverity', self.globalprevdata)
        jira_affect_version = self.prevdata('Jira.affects_version',
                                            self.globalprevdata)
        environment = self.prevdata('environment', self.globalprevdata)
        jira_watcher = self.prevdata('Jira.watcher', self.globalprevdata)
        tmproject = self.prevdata('TM_Project', self.globalprevdata)
        sprintnumber = self.prevdata('sprint_number', self.globalprevdata)
        fixversion = self.prevdata('fix_version', self.globalprevdata)
        log_level = self.prevdata('LogLevel', self.globalprevdata)
        symmetric_key = "Enter a key to encrypt/decrypt passwords [" +\
            self.prevdata('symmetric_key', self.globalprevdata) + "]: "
        symmetric_key = self.get_input(symmetric_key)
        environment = "Enter the Execution Environment [" + environment + "]: "
        environment = self.get_input(environment)        
        tmproject = "Enter Jira Test Management Project Key [" + \
            tmproject + "]: "
        tmproject = self.get_input(tmproject)
        sprintnumber = "Enter Current Sprint Name [" + \
            sprintnumber + "]: "
        sprintnumber = self.get_input(sprintnumber)
        fixversion = "Enter Jira testcase/testsuite fix version [" + \
            fixversion + "]: "
        fixversion = self.get_input(fixversion)        
        glob_details = {"symmetric_key": symmetric_key,'environment': environment,
                        'sprint_number': sprintnumber,
                        'fix_version': fixversion,
                        'TM_Project': tmproject}
        self.update_dict(self.globalfilepath, glob_details)
        enabletestmanagement = "Do you want to enable test management as jira [" +\
            self.prevdata('EnableTestManagement',
                          self.globalprevdata) + "]:(Yes/No)"
        enabletestmanagement = self.get_input(
            enabletestmanagement, choices=["yes", "no"])

        if enabletestmanagement.lower() == 'yes':
            username = "enter Jira username(EmailId)[" + username + "]:"
            username = self.get_input(username)
            password = self.get_password("enter Jira APIKEY:", password)
            jira_url = "Enter Jira URL [" + jira_url + "]: "
            jira_url = self.get_input(jira_url)            
            raise_bugs = "Do you want to enable Bug Management [" +\
                self.prevdata('Raise_Bugs', self.globalprevdata) + "]:(Yes/No)"
            raise_bugs = self.get_input(raise_bugs, choices=["yes", "no"])
            if raise_bugs.lower() == 'yes':
                jira_proj = "Enter Jira Bug Management Project [" + jira_proj + "]: "
                jira_proj = self.get_input(jira_proj)
                jirabugpriority = "Enter Jira bug priority(1:Critcical,2:High,3:Medium,4:Low,5:Trivial) [" + \
                    jirabugpriority + "]: "
                jirabugpriority = self.get_input(jirabugpriority, choices=[
                    '1', '2', '3', '4', '5'])
                jirabugseverity = "Enter Jira bug severity(1:Critcical,2:Major,3:Moderate,4:Low,5:Trivial) [" + \
                    jirabugseverity + "]: "
                jirabugseverity = self.get_input(jirabugseverity, choices=[
                    '1', '2', '3', '4', '5'])
                jira_affect_version = "Enter the Affects Version [" \
                    + jira_affect_version + "]: "
                jira_affect_version = self.get_input(jira_affect_version)
                logger.warn("By default project lead and test user "
                            "will be added as watcher")
                if jira_watcher:
                    value = 'yes'
                else:
                    value = 'no'
                    add_watcher = "Do you want to add more watcher:(Yes/No)[" + \
                        value + "]: "
                    add_watcher = self.get_input(add_watcher)
                    if add_watcher.lower() == 'yes':
                        jira_watcher = "Enter user name to add as a watcher [" +\
                            jira_watcher + "]: "
                        jira_watcher = self.get_input(jira_watcher)
                    else:
                        jira_watcher = ''
        glob_dict = {'EnableTestManagement': enabletestmanagement,
                     'Jira': {
                         'url': jira_url,
                        'project': jira_proj
                        }}
        jira_dict = {'Jira': {'username': username,
              'password': password}}
        glob_dict.update({'Raise_Bugs': raise_bugs})
        raise_bugs_dict = {'bugseverity': jirabugseverity,
                    'bugpriority': jirabugpriority, 'affects_version': jira_affect_version, 'watcher': jira_watcher,}
        glob_dict['Jira'].update(raise_bugs_dict)
        self.update_dict(self.filepath, jira_dict)
        self.update_dict(self.globalfilepath, glob_dict)
        db_dict = self.add_dbconf()
        slack_dict = self.add_slackconf()
        teams_dict = self.add_teamsconf()
        email_dict = self.add_mailconf()
        artifact_dict = self.add_artifactserverdetails()
        self.update_dict(self.filepath, db_dict[0])
        self.update_dict(self.globalfilepath, db_dict[1])
        self.update_dict(self.filepath, slack_dict[0])
        self.update_dict(self.globalfilepath, slack_dict[1])
        self.update_dict(self.globalfilepath, email_dict)
        self.update_dict(self.globalfilepath, teams_dict)
        self.update_dict(self.filepath, artifact_dict[0])
        self.update_dict(self.globalfilepath, artifact_dict[1])
        log_level = "\nEnter the log level (info or debug or warn) [" +\
            'warn' + "]:"
        log_level = self.get_input(log_level, choices=["info", "debug", "warn",
                                                       "error"])
        log_dict = {"LogLevel": log_level.lower()}

        self.update_dict(self.globalfilepath, log_dict)
        val_obj = ValidateUserConfig()
        globdata = get_data_from_yaml(self.globalfilepath)
        jiralist = []
        dblist = []
        cronlist = []
        maillist = []
        comlist = []
        comlist1 = []
        if globdata.get('Raise_Bugs','no').lower() == 'yes':
            try:
                val_obj.validate_jira()
                jiralist = ["Jira", "Validated Successfully"]
            except Exception as e:
                notify.message('`\t\t' + str(e).replace("\n", "\n\t\t") + '`')
                jiralist = ['Jira',
                            "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
        else:
            jiralist = [
                "Jira", "TestManagement is set to 'no'. Hence not validating"]

        if globdata.get('EnableDatabase','no').lower() == 'yes':
            try:
                val_obj.validate_database()
                dblist = ["Database", "Validated Successfully"]
            except Exception as e:
                notify.message('`\t\t' + str(e).replace("\n", "\n\t\t") + '`')
                dblist = ["Database",
                          "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
        else:
            dblist = ["Database",
                      "EnableDatabase is set to 'no'. Hence not validating"]

        if globdata.get('EnableTestArtifacts','no').lower() == 'yes':
            try:
                val_obj.ckeck_cronjob_in_appache_server()
                cronlist = ["TestArtifact server",
                            "Validated Successfully"]
            except Exception as e:
                notify.message('`\t\t' + str(e).replace("\n", "\n\t\t") + '`')
                cronlist = ["TestArtifact server",
                            "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
        else:
            cronlist = ["TestArtifact server",
                        "EnableTestArtifacts is set to 'no'. Hence not validating"]

        if globdata.get('EmailNotifications','no').lower() == 'yes':
            try:
                val_obj.validate_email()
                maillist = ["Email", "Validated Successfully"]
            except Exception as e:
                notify.message('`\t\t' + str(e).replace("\n", "\n\t\t") + '`')
                maillist = ["Email",
                            "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
        else:
            maillist = [
                "Email", "EmailNotifications is set to 'no'. Hence not validating"]

        msg = ''
        if globdata.get('SlackNotifications','no').lower() == 'yes' and \
                globdata.get('TeamsNotifications','no').lower() == 'yes':
            msg = "Slack and MS Teams"
        elif globdata.get('SlackNotifications','no').lower() == 'yes' and \
                globdata.get('TeamsNotifications','no').lower() == 'no':
            msg = "Slack"
            comlist1 = [
                "MS Teams", "TeamsNotifications is set to no. Hence not validating."]
        elif globdata.get('SlackNotifications','no').lower() == 'no' and \
                globdata.get('TeamsNotifications','no').lower() == 'yes':
            msg = "MS Teams"
            comlist1 = [
                "Slack", "SlackNotifications is set to no. Hence not validating."]

        if msg:
            try:
                val_obj.validate_communication_channels()
                comlist = [msg, "Validated Successfully"]
            except Exception as e:
                if "Slack" in msg and "Teams" in msg:
                    if "Slack" in e and "Teams" not in e:
                        comlist = [
                            "Slack", "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
                        comlist1 = ["MS Teams", "Validated Successfully"]
                    elif "Teams" in e and "Slack" not in e:
                        comlist = [
                            "MS Teams", "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
                        comlist1 = ["Slack", "Validated Successfully"]
                else:
                    comlist = [msg,
                               "Validation Failed with below error:\n\t\t\t" + str(e).replace("\n", "\n\t\t\t")]
        else:
            comlist = [
                "Slack", "SlackNotifications is set to no. Hence not validating."]
            comlist1 = [
                "MS Teams", "TeamsNotifications is set to no. Hence not validating."]

        msg = tabulate([jiralist, [], [], dblist, [], [], cronlist, [], [],
                        maillist, [], [], comlist, [], [], comlist1],
                       headers=['Application/Server', 'Validation status'],
                       tablefmt='pipe')
        logger.warn('\n\n' + msg)
