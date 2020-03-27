"""
    Integration module which will parse user_info file and returns slack and mail objects.
"""
import os
from os.path import expanduser
import datetime
from lib.Slacklib import Slacklib
from lib.Teamslib import Teamslib
from lib.Maillib import Maillib
from lib.SlackExceptions import SlackChannelException
from lib.SlackExceptions import SlackTokenException
from lib.MailExceptions import MailConnectionException
from lib.MailExceptions import MailRecipientsException
from lib import logger
from lib.utilities import get_data_from_yaml
from lib.singleton import singleton

count = 0

class IntConfig(object):
    """
        Gets the data from user_info file and global_conf file and provides
        that data to its child classes SlackNotification and MailNotification
    """

    def __init__(self):
        self.filepath = os.path.join(expanduser('~'), "user_info.yaml")
        self.globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
        self.glob_data = get_data_from_yaml(self.globalfilepath)
        self.data = get_data_from_yaml(self.filepath)


@singleton
class SlackNotification(IntConfig):
    """
        Inherits IntConfig class and provides data to slackobj method.
    """

    def slackobj(self):
        """
            Returns slackobj if user provides correct data otherwise raises Exception
        """
        try:
            if self.glob_data['SlackNotifications'].lower() == 'yes':
                if "Slack" in self.glob_data:
                    username = self.data['Slack']['username']
                    channelname = self.glob_data['Slack']['channelname']
                    token = self.data['Slack']['token']
                    if not channelname or channelname == 'None':
                        logger.warn("ChannelName is not provided \
                                    hence not sending mail notifications")
            else:
                return Message()
        except KeyError:
            logger.warn("SlackNotifications are disabled")

        try:
            slkobj = Slacklib(username, channelname, slack_token=token)
            return slkobj
        except SlackChannelException as e:
            logger.warn(e.message)
            return Message()
        except SlackTokenException as e:
            logger.warn(e.message, console=False)
            raise SlackTokenException(e.message)
        except Exception as e:
            logger.warn(e.message)
            return Message()


@singleton
class TeamsNotification(IntConfig):
    """
        Inherits IntConfig class and provides data to slackobj method.
    """

    def teamsobj(self):
        """
            Returns slackobj if user provides correct data otherwise raises Exception
        """
        try:
            if self.glob_data['TeamsNotifications'].lower() == 'yes':
                if "Teams" in self.glob_data:
                    url = self.glob_data['Teams']['url']
            else:
                return Message()
        except KeyError:
            logger.warn("TeamsNotifications are disabled")

        try:
            tmsobj = Teamslib(url)
            return tmsobj
        except Exception as e:
            logger.warn(e.message)
            return Message()


@singleton
class EmailNotification(IntConfig):
    """
        Inherits IntConfig class and provides data to emailobj method.

    """

    def emailobj(self):
        """
            Returns mailobj if user provides correct data otherwise raises Exception
        """
        try:
            if self.glob_data['EmailNotifications'].lower() == 'yes':
                if "Email" in self.glob_data:
                    recipients = self.glob_data['Email']['recipients']
                    if not recipients or recipients == 'None':
                        logger.warn("Recipients list is not provided hence \
                                    not sending email notifications")
            else:
                return Message()
        except KeyError:
            logger.warn('MailNotifications are disabled')

        try:
            emailobj = Maillib(recipients)
            return emailobj
        except MailConnectionException as err:
            logger.warn(err.message)
            return Message()
        except MailRecipientsException as err:
            logger.warn(err.message)
            return Message()


class Message(object):
    """
    This class is used when slack or teams notifications are disabled in
    global config file.

    """

    def send_message(self):
        """
        Duplicate send_message for Slacklib class
        """
        return "success"

    def consolidate_messages(self, msg):
        """
        This method is used when slack or teams notification is "no" in global_conf.yaml file.
        """

    def message(self, msg):
        """
        This method is used when slack or teams notification is "no" in global_conf.yaml file.
        """
        if not os.environ.get("sutasmessages"):
            os.environ["sutasmessages"] = ""
        os.environ["sutasmessages"] = os.environ[
            "sutasmessages"] + "\r\n" + msg

    def send_mail(self, subject):
        """
        Duplicate send_message method for Maillib class
        """
        pass
    
    def send_mail_when_failed(self, body):
        """
        Duplicate send_mail_when_failed method for Maillib class
        """
        pass

class notify(object):
    """
    Creates slack,teams and mail obj which can be imported where ever required
    Eg:from lib.IntConfig import notify
    and call method notify.send_message(msg) this will send notification
    to the slack and teams channels.
    If you want to send mail notifications then you need to use
    notify.send_mail(msg)
    Note:msg is the custom message that will be appeared in slack channel
    """

    @staticmethod
    def send_message():
        """
        Creates slackobj and sends consolidated slack message
        """
        global count
        sutasfolder = os.path.join(os.path.expanduser('~'), "Sutas_Logs")
        slckobj = SlackNotification().slackobj()
        slc = slckobj.send_message()
        tmsobj = TeamsNotification().teamsobj()
        tms = tmsobj.send_message()
        globfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
        globdata = get_data_from_yaml(globfilepath)
        if "logpath" in os.environ:
            # getting the testsuite name from logpath
            mailfile = os.path.basename(os.environ['logpath']).split(
                str(datetime.datetime.now().year))[0]
            # Inside testsuite folder in sutaslogs we are creating a file with
            # testsuite name. This file will be used to store the notification
            # messages
            mailfile = os.path.join(os.path.dirname(os.environ['logpath']),
                                    mailfile)
            if os.path.isfile(mailfile):
                if count == 0:
                    os.remove(mailfile)
                    count = 1
            # suitelogpaths file is created in sutaslog folder which is
            # in user's home directory.
            suitelogpaths = os.path.join(sutasfolder, "suitelogpaths")
            flag = False
            
            if globdata.get('Consolidatedmail','no').lower() == 'yes':
                mode = "a"
            else:
                mode = "w"
            # Checks if suitelogpath file already exists.
            if os.path.isfile(suitelogpaths):
                # checking if the logpath is already in the suitelogpaths file.
                # if path exists then continue else writes the path in to file.
                with open(suitelogpaths, 'r') as suite:
                    for line in suite.read().strip().splitlines():
                        if os.environ['logpath'] in line:
                            flag = True
                if not flag:
                    with open(suitelogpaths, mode) as suite:                        
                        suite.write(os.environ['logpath'])
                        suite.write('\n')
            else:
                # creates suitelogpaths file if doesn't exist and writes
                # log path in to it.
                with open(suitelogpaths, mode) as suite:                   
                    suite.write(os.environ['logpath'])
                    suite.write('\n')
            #writing notification messages in to a testsuite file which is
            #created in testsuite folder.
            with open(mailfile, 'a') as agg:
                agg.write(os.environ["sutasmessages"])
            os.environ["sutasmail"] = os.environ["sutasmessages"]
            os.environ["sutasmessages"] = ""
        msgs = {"slack": slc, "teams": tms}
        if slc != "success" or tms != "success":
            return msgs
        else:
            return "success"

    @staticmethod
    def message(msg):
        """
        Append message to "sutasmessages" environmental variable.

        Creates "sutasmessages" environmental varialble if already doesn't
        exist. Appends messages to environmental varialbles.

        - **parameters**, **types**, **return** and **return types**::

            :param msg:custom message to be appeared in communication channels.
            :type msg: String

        """
        if "sutasmessages" not in os.environ:
            os.environ["sutasmessages"] = msg
        else:
            os.environ["sutasmessages"] = os.environ[
                "sutasmessages"] + "\r\n" + msg

    @staticmethod
    def send_mail(subject):
        """
        Creates slackobj and sends mail to list of recipients provided in
        user_info file.

        - **parameters**, **types**, **return** and **return types**::

            :param subject: Subject of the email
            :type subject: String

        """
        obj = EmailNotification().emailobj()
        obj.send_mail(subject)
