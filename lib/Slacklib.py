"""
Slack Library to send notifications while running test suite through SUTAS
"""
import os, sys
import datetime
from os.path import expanduser
#from slackclient import SlackClient
from slack import WebClient
from lib.AESCipher import AESCipher as aes
from lib.SlackExceptions import *
from lib import logger
from lib.utilities import get_data_from_yaml
flag = False


class Slacklib(object):
    """
    Slack library to post messages to slack channel after running test suites
    """

    def __init__(self, username, channelname, slack_token):
        """
        Initialize the Slacklib class
        - **parameters**, **types**, **return** and **return types**::
                param username     : username of the slack member who runs the test suite
                param channelname  : Channel to which notifications will be sent
                param slack_token  : Slack_token of user
                type username: String
                type channelname: String
                type slack_token: String
        """
        self.channelname = channelname
        self.username = username
        try:
            #slack token of user in that channel for sending notifications.
            slack_token = aes().decrypt(slack_token)
        except Exception as e:
            logger.warn("Invalid slack token")
        #self.slk = SlackClient(slack_token)
        self.slk = WebClient(token=slack_token)
        self.channelid = self.get_channelid()
        self.message = ""
        self.globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
        self.glob_data = get_data_from_yaml(self.globalfilepath)


    def get_channelid(self):
        """
        Returns channel id of the user provided channel
        - **parameters**, **types**, **return** and **return types**::
                return: channel id
                rtype: String
        """
        channel_id = None
        #If valid token is provided it will have 'channels' key
        if 'channels' not in self.slk.api_call("channels.list"):
            raise SlackTokenException
        #Getting channel id using channel name.
        #Channel id is required for sending notifications.
        for i in self.slk.api_call("channels.list")['channels']:
            if i['name'] == self.channelname:
                channel_id = i['id']
                return channel_id
        if channel_id is None:
            raise SlackChannelException

    def send_message(self):
        """
        Sends consolidated message to the Slack Teams.
        Global variable message contains conosolidated messages.
        This consolidated message will be sent to Slack Teams
        - **parameters**, **types**, **return** and **return types**::
                :return: Success string or error message
                :rtype: String
        """
        global flag
        message = os.environ.get("sutasmessages")
        if message:
            if flag:
                suitename = os.path.basename(os.environ['logpath']).split(
                        str(datetime.datetime.now().year))[0]
                #Customizing slack notifications using hash
                hash = "######################################"
                message = "\n" + 2*hash + "\n\t\t" + suitename + "\n" + 2*hash + "\n" + message + "\n"
                flag = False
            else:
                flag = True
            if self.glob_data['SlackNotifications'].lower()=='yes':
                req = self.slk.api_call("chat.postMessage", channel="%s" %self.channelid, text="%s" %message,username="%s" %self.username)

                if req["ok"]:
                    return "success"
                else:
                    return req["error"]
        else:
            logger.warn("No messages to send.")
