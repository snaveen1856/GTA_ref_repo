import os
import sys
import yaml
from os.path import expanduser
from lib import logger
from lib.AESCipher import AESCipher
from lib.ValidateUserConfig import ValidateUserConfig
from lib.utilities import dump_data_into_yaml, get_data_from_yaml


class jenkinsetup(object):
    """
    This class implements the SUTAS user setup.
    """

    def __init__(self, args):
        """
        Gets the data from user_info and global_conf file yaml files

        - **parameters**, **types**, **return** and **return types**::

            param args: commandline arguments
            type args: List
        """
        self.args = args
        self.filepath = os.path.join(expanduser('~'), "user_info.yaml")
        self.globalfilepath = os.path.join(expanduser('~'),
                                           "global_conf.yaml")
        self.userprevdata = self._userdata()
        self.globalprevdata = self._globaldata()
        self.dump_data()

    def _update_dict(self, filename, new_dict):
        """
        Updates the global conf file.
        - **parameters**, **types**, **return** and **return types**::

            param filename: name of the file
            type filename: String
            param new_dict: dictionary with which file will be updated
            type new_dict: dictionary
        """
        if os.path.exists(filename):
            old_dict = get_data_from_yaml(filename)
            yamldict = old_dict.copy()
            yamldict.update(new_dict)
        else:
            yamldict = new_dict
        dump_data_into_yaml(filename, yamldict, mode="w")

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
            data = ""
        finally:
            return data

    def _globaldata(self):
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

    def _userdata(self):
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

    def dump_data(self):
        """
        This will dump the data taken from commandline arguments
        in to config files and validates the data.
        """
        slacktoken = ''
        jirapwd = ''
        dbpassword = ''
        dbserverpwd = ''
        if self.prevdata('Slack.token', self.userprevdata):
            slacktoken = AESCipher().decrypt(self.prevdata('Slack.token',
                                                           self.userprevdata))
        if self.prevdata('Jira.password', self.userprevdata):
            jirapwd = AESCipher().decrypt(self.prevdata('Jira.password',
                                                        self.userprevdata))
        if self.prevdata('Database.pwd', self.userprevdata):
            dbpassword = AESCipher().decrypt(self.prevdata('Database.pwd',
                                                           self.userprevdata))
        if self.prevdata('Database.serverpassword', self.userprevdata):
            dbserverpwd = AESCipher().decrypt(self.prevdata(
                'Database.serverpassword',
                self.userprevdata))
        if self.prevdata('TestArtifact.password', self.userprevdata):
            testartifactspwd = AESCipher().decrypt(self.prevdata(
                'TestArtifact.password',
                self.userprevdata))
        else:
            testartifactspwd = ''

        userargs = {'symmetrickey': self.prevdata('symmetric_key',
                                                  self.globalprevdata),
                    'raisebugs': self.prevdata('Raise_Bugs',
                                               self.globalprevdata),
                    'jiraurl': self.prevdata('Jira.url',
                                             self.globalprevdata),
                    'jirausr': self.prevdata('Jira.username',
                                             self.userprevdata),
                    'jirapwd': jirapwd,
                    'jira_affect_version': self.prevdata('Jira.affects_version',
                                                         self.globalprevdata),
                    'jira_watcher': self.prevdata('Jira.watcher',
                                                  self.globalprevdata),
                    'jiraenv': self.prevdata('environment',
                                             self.globalprevdata),
                    'jiraproj': self.prevdata('Jira.project',
                                              self.globalprevdata),
                    'jirabugpriority': self.prevdata('Jira.bugpriority', self.globalprevdata),
                    'jirabugseverity': self.prevdata('Jira.bugseverity', self.globalprevdata),
                    'slack': self.prevdata('SlackNotifications',
                                           self.globalprevdata),
                    'slacktoken': slacktoken,
                    'slackusr': self.prevdata('Slack.username',
                                              self.userprevdata),
                    'slackchannel': self.prevdata('Slack.channelname',
                                                  self.globalprevdata),
                    'loglevel': self.prevdata('LogLevel', self.globalprevdata),
                    'emailnotifications': self.prevdata('EmailNotifications',
                                                        self.globalprevdata),
                    'emails': self.prevdata('Email.recipients',
                                            self.globalprevdata),
                    'validateemails': self.prevdata('Email.ValidateEmails', self.globalprevdata),
                    'smtpip': self.prevdata('Email.smtpip',
                                            self.globalprevdata),
                    'smtpport': self.prevdata('Email.smtpport',
                                              self.globalprevdata),
                    'consolidatedmail': self.prevdata('Consolidatedmail',
                                                      self.globalprevdata),
                    'send_mail_only_if_failed': self.prevdata('send_mail_only_if_failed',
                                                              self.globalprevdata),
                    'teamsnotifications': self.prevdata('TeamsNotifications',
                                                        self.globalprevdata),
                    'teamsurl': self.prevdata('Teams.url', self.globalprevdata),
                    'enabledatabase': self.prevdata('EnableDatabase',
                                                    self.globalprevdata),
                    'dbusername': self.prevdata('Database.username',
                                                self.userprevdata),
                    'dbpassword': dbpassword,
                    'databasename': self.prevdata('Database.database_name',
                                                  self.globalprevdata),
                    'dbserverip': self.prevdata('Database.serverip',
                                                self.globalprevdata),
                    'dbserveruser': self.prevdata('Database.serverusername',
                                                  self.userprevdata),
                    'dbserverpwd': dbserverpwd,
                    'serverostype': self.prevdata('Database.serverOStype',
                                                  self.globalprevdata),
                    'dbprune': self.prevdata('Database.prune',
                                             self.userprevdata),
                    'enabletestmanagement': self.prevdata('EnableTestManagement',
                                                          self.globalprevdata),
                    'sprintnumber': self.prevdata('sprint_number',
                                                  self.globalprevdata),
                    'fixversion': self.prevdata('fix_version',
                                                self.globalprevdata),
                    'tm_project': self.prevdata('TM_Project', self.globalprevdata),
                    'enablepushtestartifacts': self.prevdata('EnableTestArtifacts',
                                                             self.globalprevdata),
                    'testaritfactsserverip': self.prevdata('TestArtifact.serverip',
                                                           self.globalprevdata),
                    'testaritfactsserveruser': self.prevdata('TestArtifact.susername',
                                                             self.userprevdata),
                    'testaritfactsserverpwd': testartifactspwd

                    }
        for key, value in list(vars(self.args).items()):
            if value:
                value = value.replace('"','')
                value = value.replace("'",'')
            userargs[key] = value
        for key, value in list(userargs.items()):
            if str(userargs[key]).lower().strip() == 'none':
                userargs[key] = None
        passwordlist = ['jirapwd', 'dbserverpwd',
                        'dbpassword', 'testaritfactsserverpwd']
        flag = False
        for key in userargs:
            if key in passwordlist:
                flag = True
                break
        if flag:
            if not userargs['symmetrickey']:
                raise Exception("--symmetrickey is mandatory when --jirapwd "
                                "or --dbserverpwd or --dbpassword or"
                                "--testaritfactsserverpwd is used")

        glob_details = {"symmetric_key": userargs['symmetrickey'],
                        'sprint_number': userargs['sprintnumber'],
                        'fix_version': userargs['fixversion'],
                        'TM_Project': userargs['tm_project'],
                        'environment': userargs['jiraenv']}
        self._update_dict(self.globalfilepath, glob_details)
        password = AESCipher().encrypt(userargs['jirapwd'])
        try:
            project = eval(userargs['jiraproj'])
        except SyntaxError as TypeError:
            project = userargs['jiraproj']
        global_dict = {'Raise_Bugs': userargs['raisebugs'],
                       'EnableTestManagement': userargs['enabletestmanagement'],
                       'Jira': {
                           'url': userargs['jiraurl'],
                           'project': project,
                           'bugseverity': userargs['jirabugseverity'],
                           'bugpriority': userargs['jirabugpriority'],
                           'affects_version': userargs['jira_affect_version'],
                           'watcher': userargs['jira_watcher']
                       }}
        logger.warn(global_dict)
        jira_dict = {'Jira': {'username': userargs['jirausr'],
                              'password': password}}     
        self._update_dict(self.filepath, jira_dict)
        self._update_dict(self.globalfilepath, global_dict)
        token = AESCipher().encrypt(userargs['slacktoken'])
        slack_dict = {
            'Slack': {'username': userargs['slackusr'], 'token': token}}
        globalslack_dict = {'SlackNotifications': userargs['slack'],
                            'Slack': {'channelname': userargs['slackchannel']}}
        globalteams_dict = {'TeamsNotifications': userargs['teamsnotifications'],
                            'Teams': {'url': userargs['teamsurl']}}
        email_dict = {'EmailNotifications': userargs['emailnotifications'],
                      'Email': {'recipients': userargs['emails'],
                                'ValidateEmails': userargs['validateemails'],
                                'smtpip': userargs['smtpip'],
                                'smtpport': userargs['smtpport']},
                      'Consolidatedmail': userargs['consolidatedmail'],
                      'send_mail_only_if_failed':userargs['send_mail_only_if_failed']}
        dbpassword = AESCipher().encrypt(userargs['dbpassword'])
        dbserverpwd = AESCipher().encrypt(userargs['dbserverpwd'])
        db_dict = {'Database': {'username': userargs['dbusername'],
                                'pwd': dbpassword,
                                'serverusername': userargs['dbserveruser'],
                                'serverpassword': dbserverpwd}
                   }
        globdb_dict = {'EnableDatabase': userargs['enabledatabase'],
                       'Database': {'database_name': userargs['databasename'],
                                    'serverip': userargs['dbserverip'],
                                    'prune': userargs['dbprune'],
                                    'serverOStype': userargs['serverostype']}
                       }
        
        globtestartifacts_dict = {'EnableTestArtifacts': userargs['enablepushtestartifacts'],
                                  'TestArtifact':
                                  {'serverip': userargs['testaritfactsserverip']}, }
        testartifactspwd = AESCipher().encrypt(
            userargs['testaritfactsserverpwd'])
        testartifacts_dict = {'TestArtifact': {'username': userargs['testaritfactsserveruser'],
                                               'password': testartifactspwd}}
        '''
        create and update dict for test environment variable
        '''
        self._update_dict(self.filepath, slack_dict)
        self._update_dict(self.globalfilepath, globalslack_dict)
        self._update_dict(self.globalfilepath, globalteams_dict)
        self._update_dict(self.globalfilepath, email_dict)
        self._update_dict(self.filepath, db_dict)
        self._update_dict(self.globalfilepath, globdb_dict)
        self._update_dict(self.globalfilepath, globtestartifacts_dict)
        self._update_dict(self.filepath, testartifacts_dict)
        if not vars(self.args)['loglevel']:
            userargs['loglevel'] = 'warn'
        log_dict = {"LogLevel": userargs['loglevel']}
        self._update_dict(self.globalfilepath, log_dict)
        val_obj = ValidateUserConfig()
        val_obj.validate_jira()
        val_obj.validate_database()
        val_obj.ckeck_cronjob_in_appache_server()
        val_obj.validate_email()
        val_obj.validate_communication_channels()
