"""
Teams Library to send notifications while running test suite through SUTAS
"""
import os
import requests
from os.path import expanduser
from requests.exceptions import ConnectionError
from lib import logger
from lib.utilities import get_data_from_yaml

flag = False


class Teamslib(object):
    """
    Teams library to post messages to slack channel after running test suites
    """

    def __init__(self, url):
        """
        Initialize the Teamslib class
        - **parameters**, **types**, **return** and **return types**::

            :param url: url of the incoming webhook configured in MS Teams
            :type url: String
        """
        self.url = url
        self.globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")
        self.glob_data = get_data_from_yaml(self.globalfilepath)

    def send_message(self):
        """
        Sends consolidated message to the MS Teams.
        Global variable message contains conosolidated messages.
        This consolidated message will be sent to MS Teams
        - **parameters**, **types**, **return** and **return types**::
                :return: Success string or error message
                :rtype: String
        """
        global flag
        message = os.environ.get("sutasmessages")
        if message:
            if flag:
                hash = "######################################"
                message = "\n" + 2*hash + message + 2*hash + "\n"
                flag = False
            else:
                flag = True
            if self.glob_data['TeamsNotifications'].lower()=='yes':
                data = {"text":message}
                try:
                    req = requests.post(self.url, json=data)
                    if req.status_code != 200:
                        logger.warn("Failed to send messages to Teams.")
                        logger.warn(str(req.text))
                        return str(req.text)
                    else:
                        return "success"
                except ConnectionError:
                    msg = "Failed to establish connection with MS Teams"
                    logger.warn(msg)
                    return msg
        else:
            logger.warn("No messages to send.")

