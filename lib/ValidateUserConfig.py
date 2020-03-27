from jira.client import JIRA,JIRAError
from lib.Jiralib import Jiralib
from lib.IntConfig import notify
from lib import logger
from lib.models import db_session
from lib.SSH import SSH
from lib.Maillib import Maillib
from sqlalchemy.exc import OperationalError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from lib.AESCipher import AESCipher as aes
from os.path import expanduser
from distutils import sysconfig
import os
import requests
import yaml
import smtplib
from lib.utilities import get_data_from_yaml,fetch_data_from_testenvdata
import paramiko
import base64
from lib.exceptions import EnvException,TMDBException
from lib.IntConfig import EmailNotification,Message
import sys

class ValidateUserConfig(object):
    """
    Fetches user_info.yaml and Validates jira,slack,mail details
    """
    def __init__(self):
        self.filepath = os.path.join(expanduser('~'), "user_info.yaml")
        self.globfilepath = os.path.join(expanduser('~'), "global_conf.yaml")

    def validate_jira(self):
        """
        Validates Jira user inputs
        Checks Connection to jira.If connection refused it raises exception.
        Checks user authentication to jira.If authentication failed it
        raises exception
        Checks project version with affects_version provided in user_info
        file and raises exception if not matches
        """
        data = get_data_from_yaml(self.filepath)
        globdata = get_data_from_yaml(self.globfilepath)
        if globdata.get('EnableTestManagement','no').lower() == 'yes':
            if globdata.get("Jira"):
                jira = globdata.get("Jira")
            else:
                raise Exception("Failed to validate jira details.Please re-run sutas user_setup")
            if data.get("Jira"):
                jira_cred = data.get("Jira")
            else:
                raise Exception("Failed to validate jira details.Please re-run sutas user_setup")
            url = jira.get("url")
            user_name = jira_cred.get("username")
            pwd = jira_cred.get("password")
            proj = jira.get("project")
            watcher = jira.get("watcher")
            fix_version = globdata.get("fix_version")
            env = globdata.get("environment")
            TM_proj = globdata.get("TM_Project")
            # validate Jira url
            logger.warn("Validating JIRA details...........")
            notify.message("*Validating JIRA details.*")
            try:
                response = requests.get(url)
                obj = Jiralib(url, user_name, pwd)
                conn = obj.conn
                user = user_name.split('@')[0]
                if not conn.user(user) or response.status_code != 200:
                    log_msg = "Unable to connect to Jira URL"
                    logger.warn(log_msg)
                    notify.message(log_msg)
                    raise Exception(log_msg)
            except Exception as e :
                logger.error("Not able to connect to jira with the credentials Given")
                raise e
            TM_project_found = False
            for i in conn.projects():
                if i.key == TM_proj:
                    TM_project_found = True
                    logger.warn("TestManagement Project {} found in Jira".format(TM_proj))
                    break
            if not TM_project_found:
                log_msg = "Given TestManagement Project key {} not found in Jira. Please re-rerun"\
                    " user setup with valid inputs".format(TM_proj)
                logger.warn(log_msg)
                notify.message(log_msg)
                raise Exception(log_msg)
            # validate jira users
            if watcher:
                users = watcher.split(",")
                for user in users:
                    try:
                        jira_user = conn.user(user)
                    except JIRAError:
                        jira_user = None
                    if not jira_user:
                        log_msg = "User {} not found in Jira to add as "\
                            "watcher. Please re-reun"\
                            " user setup with valid inputs".format(user)
                        logger.warn(log_msg)
                        notify.message(log_msg)
                        raise Exception(log_msg)
            try:
                if fix_version:
                    # validate Jira fields
                    versions = conn.project_versions(TM_proj)
                    version_found = False
                    for version in versions:
                        if fix_version == version.name:
                            version_found = True
                            logger.warn("FixVersion {} found in jira project {}".format(fix_version,TM_proj))
                            break
                    if not version_found:
                        log_msg = "Version {} not found in jira project." \
                            "Please provide "\
                            "valid version.".format(fix_version)
                        logger.warn(log_msg)
                        notify.message(log_msg)
                        raise Exception(log_msg)
            except Exception as e:
                raise e
            self.validate_bug_management_details(conn)
        else:
            logger.info("TestManagement is disabled.Hence not validating JIra Details")
                

    def validate_communication_channels(self):
        """
        Validates Slack user inputs
        Checks for valid token,channelname.
        If invalid token or channel name found SUTAS raises SlackExceptions.
        """
        globdata = get_data_from_yaml(self.globfilepath)
        msg = ''
        if globdata.get('SlackNotifications','no').lower() == 'yes' and \
           globdata.get('TeamsNotifications','no').lower() == 'yes':
            msg = "*Validating Slack and Microsoft Teams details.*"
        elif globdata.get('SlackNotifications','no').lower() == 'yes' and \
             globdata.get('TeamsNotifications','no').lower() == 'no':
            msg = "*Validating Slack details.*"
        elif globdata.get('SlackNotifications','no').lower() == 'no' and \
             globdata.get('TeamsNotifications','no').lower() == 'yes':
            msg = "*Validating Microsoft Teams details.*"
        elif globdata.get('SlackNotifications','no').lower() == 'no' and \
             globdata.get('TeamsNotifications','no').lower() == 'no':
            msg = "*Notifications are disabled hence not validating.*"
        logger.warn(msg)
        notify.message(msg)
        result = notify.send_message()
        if result != "success":
            msg = {i:result[i] for i in result if result[i] != "success" and not result[i]}
            if msg:
                if len(msg)>1:
                    errmsg = "Slack failed with error: %s \n" +\
                        "Teams failed with error: %s" %(msg["slack"],
                                                        msg["teams"])
                else:
                    errmsg = "%s failed with error: %s" %(list(msg.keys())[0],
                                                          list(msg.values())[0])
                raise Exception(errmsg)


    def validate_database(self):
        """
        Validates database details.
        """
        globdata = get_data_from_yaml(self.globfilepath)
        userdata = get_data_from_yaml(self.filepath)
        if globdata.get('EnableDatabase','no').lower() == 'yes':
            logger.warn("Validating database details.")
            notify.message("*Validating database details.*")
            try:
                db_session()
            except OperationalError as e:
                msg = ("\n\nCOULD NOT CONNECT TO SERVER. "
                       "PLEASE CHECK DETAILS.\n")
                logger.warn(msg)
                notify.message(msg)
                logger.error(msg)
                raise Exception(e)
            except Exception as e:
                logger.error(str(e))
                notify.message(str(e))
                raise Exception(str(e))
            if globdata['Database']['prune'].lower() == 'yes':
                logger.warn("Validating database SERVER details")
                notify.message("Validating database SERVER details")
                ip = globdata['Database']['serverip']
                username = userdata['Database']['serverusername']
                pwd = userdata['Database']['serverpassword']
                pwd = aes().decrypt(pwd)
                self.sshclient = SSH(ip, username=username, password=pwd)
                try:
                    self.sshclient.connect()
                except Exception as e:
                    logger.warn("Validation on DB SERVER details failed.")
                    notify.message("Validation on DB SERVER details failed.")
                    logger.error(str(e))
                    raise Exception(str(e))
        else:
            logger.warn("EnableDatabase is set to 'no' hence "
                        "not verifying database details")
            notify.message("EnableDatabase is set to 'no' hence "
                           "not verifying database details")

    def ckeck_cronjob_in_appache_server(self):
        """
        Thhis function is responsible to establish connect to appache server and checks
        cronjob(triggers a delete_artifacts script on every week) entry, If there was no cron job
        then it will add cron job. And it will check delete_artifacts.py file is existed or not, if file
        was not there then it will copy the file from sutas to appache server.
        """
        filepath = os.path.join(os.path.expanduser('~'), "user_info.yaml")
        globalfilepath = os.path.join(os.path.expanduser('~'),
                                      "global_conf.yaml")
        userdata = get_data_from_yaml(filepath)
        glob_data = get_data_from_yaml(globalfilepath)
        if glob_data['EnableTestArtifacts'].lower() == 'yes':
            logger.warn("Validating testartifact server details")
            notify.message("*Validating testartifact server details*")
            self.path = '/var/www/html/sutas-logs/'
            server = glob_data['TestArtifact']['serverip']
            username= userdata['TestArtifact']['username']
            password = aes().decrypt(
                userdata['TestArtifact']['password'])
            path = '/var/www/html/sutas-logs/'
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server,username=username,password=password)
            stdip, stdout, stderr = ssh.exec_command('crontab -l')
            stdi, stdo, stder = ssh.exec_command('ls ~/delete_artifacts.py')
            if not stdo.read():
                sftp = ssh.open_sftp()
                site_packages_path = sysconfig.get_python_lib()
                with open(os.path.join(site_packages_path,'easy-install.pth'), 'r') as pthdata:
                    data = pthdata.readlines()
                    for line in data:
                        line = line.strip('\n')
                        if 'sutas' in line:
                            sutaspath = os.path.basename(line)
                file_path = os.path.join(site_packages_path, sutaspath)
                source = os.path.join(os.path.join(file_path, 'tools'), 'delete_artifacts.py')
                homedir = '/home/%s' %username
                sftp.put(source, homedir+"/delete_artifacts.py")
                sftp.close()
            if not 'delete_artifacts.py' in stdout.read():
                stdip, stdout, stderr = \
                    ssh.exec_command('(crontab -l ; echo "59 23 * * * /usr/bin/python ~/delete_artifacts.py >> ~/artifacts.log 2>&1") | crontab -')
        else:
            logger.warn("EnableTestArtifacts is set to 'no' in global_conf "
                        "hence not validating apache server connection")
            notify.message("EnableTestArtifacts is set to 'no' in global_conf "
                           "hence not validating apache server connection")

    def validate_email(self):
        """
        Validating email details.
        """
        globdata = get_data_from_yaml(self.globfilepath)
        userdata = get_data_from_yaml(self.filepath)
        if globdata.get('EmailNotifications','none').lower() == 'yes':
            logger.warn("Validating Email details.")
            notify.message("*Validating Email details.*")
            if "Email" in globdata:
                recipients = globdata['Email']['recipients']
                if not recipients or recipients == 'None':
                    logger.warn("Recipients list cannot be empty when 'EmailNotifications' is yes")
                    notify.message("Recipients list cannot be empty when 'EmailNotifications' is yes")
            if globdata["Email"]['ValidateEmails'].lower() == 'yes':
                smtpip = globdata["Email"]["smtpip"]
                smtpport = globdata["Email"]["smtpport"]
                mailconn = smtplib.SMTP(smtpip, int(smtpport))
                msg = MIMEMultipart()
                msg['From'] = "sutas@sungardas.com"
                recipients = globdata["Email"]['recipients']
                msg['To'] = recipients
                recipients = recipients.split(',')
                msg['Subject'] = "Email validation by SUTAS."
                body = '''*** This is an automatically generated mail.It's been sent while running "sutas user_setup" for validating email.
                It validates smtp server details and email recipients details provided by user.Please ignore and do not reply......***'''
                msg.attach(MIMEText(body, 'plain'))
                text = msg.as_string()
                mailconn.sendmail('sutas@sungardas.com', recipients , text)
            else:
                logger.warn("ValidateEmails is set to 'no' in global_conf hence "
                                    "not sending emails to recipients.")                
        else:
            logger.warn("EmailNotifications is set to 'no' in global_conf hence "
                        "not validation email details")
            notify.message("EmailNotifications is set to 'no' in global_conf hence "
                           "not validation email details")

    def validate_env(self):
        logger.warn("Validating Environment.......")
        globdata = get_data_from_yaml(self.globfilepath)
        userdata = get_data_from_yaml(self.filepath)
        if globdata.get('EnableTestManagement').lower() == "yes":
            if "Jira" in globdata:
                envlist = fetch_data_from_testenvdata('envlist')
                try:
                    exec_env = globdata.get('environment')
                    if exec_env not in envlist:
                        raise EnvException
                    else:
                        logger.warn("ENVIRONMENT Validation successful")
                except EnvException as err:
                    mailobj = EmailNotification().emailobj()
                    body = "Provided Execution Environment is {}".format(exec_env)
                    body += '\n' + "Execution Environment must be specified from one of the following values"+ '\n' + "{}".format(envlist)
                    mailobj.send_mail_when_failed(body)
                    logger.error(body)
                    sys.exit(1)
    def validate_bug_management_details(self,conn):
        globdata = get_data_from_yaml(self.globfilepath)
        userdata = get_data_from_yaml(self.filepath)
        proj = globdata['Jira']['project']
        affects_version = globdata['Jira']['affects_version']
        if globdata.get('Raise_Bugs').lower() == "yes":
            BM_project_found = False
            for i in conn.projects():
                if i.name == proj:
                    BM_project_found = True
                    logger.warn("BugManagement Project {} found in Jira".format(proj))
                    break
            if not BM_project_found:
                log_msg = "Given BugManagement Project key {} not found in Jira. Please re-rerun"\
                    " user setup with valid inputs".format(proj)
                logger.warn(log_msg)
                notify.message(log_msg)
                raise Exception(log_msg)
