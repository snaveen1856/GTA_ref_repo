"""
Sutas generated report.html,log.html,output.xml for each test suite and
also log files for each test case.
All log files will be archived as a tar file and push it to webserver
"""
import os
import glob
import time
import tarfile
import paramiko
import base64
from lib import logger
from lib.AESCipher import AESCipher
from lib.utilities import (get_data_from_yaml,
                           check_diskusage)
created = False


class TestArtifact(object):
    """
    Class for generating Tar file and uploading file to Web Server

    Example Test artifacts file location in web server.
    Eg:http://172.16.0.190/sutas-logs/13April2017_Logs/FAS_test_suite.robot20170417_095204.tar

    Artifacts can be located through browser at http://ipaddressofserver/sutas-logs/
    """

    def __init__(self, logfilepath):
        """
            Gets username,password and ipaddress of webserver

            - **parameters**, **types**, **return** and **return types**::

                param logfilepath: file path to be pushed to web server
                type logfilepath: String
        """
        #filepath is user_info.yaml file path
        #globalfilepath is global_conf.yaml file path
        filepath = os.path.join(os.path.expanduser('~'), "user_info.yaml")
        globalfilepath = os.path.join(os.path.expanduser('~'),
                                      "global_conf.yaml")
        userdata = get_data_from_yaml(filepath)
        self.glob_data = get_data_from_yaml(globalfilepath)        
        self.path = '/var/www/html/sutas-logs/'
        #Eg:logfilepath "C:\Users\admin\Sutas_Logs\test_suite_980_2017Sep18_162033\log.html"
        self.source = logfilepath
        self.serverip = self.glob_data['TestArtifact']['serverip']
        self.username = userdata['TestArtifact']['username']
        if self.glob_data['EnableTestArtifacts'].lower() == "yes":
            self.password = AESCipher().decrypt(
                userdata['TestArtifact']['password'])
    
        
    def check_diskspace(self):
        '''Checks the diskspace available on artifactory server'''
        if self.glob_data['EnableTestArtifacts'].lower() == "yes":
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                #Establishes a connection to Linux machine
                ssh.connect(self.serverip, username=self.username, 
                            password=self.password)
            except Exception as err:
                if 'Authentication failed' in err:
                    msg = 'Check username and password of Webserver'
                    logger.error(msg)
                    #raise Exception(msg)
                else:
                    msg = ""
                    logger.error(str(err))
            else:
                logger.info('Checking disk space on test artifacts server.. ')
                if check_diskusage(ssh):
                    logger.warn('Please remove some files from '
                                'artifactory server..')

    def push_artifacts(self):
        """
            Connects to apache web server and creates a directory named with timestamp and
            place log files into that directory
        """
        if self.glob_data['EnableTestArtifacts'].lower() == "yes":
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            msg = 'ssh'
            try:
                #create connection to Linux apache server
                ssh.connect(self.serverip, username=self.username,
                            password=self.password)
            except Exception as err:
                if 'Authentication failed' in err:
                    msg = 'Check username and password of Webserver'
                    logger.warn(msg)
                    raise Exception(msg)
                else:
                    msg = ""
                    logger.warn(str(err))
            if msg == 'ssh':
                sftp = ssh.open_sftp()
                timestamp = time.strftime("%d%b%Y")
                #Ex:suite_name FAS_test_suite2017Aug11_162033
                if self.source:
                    suite_name = os.path.basename(os.path.dirname(self.source))
##                    if 'consolidated' in self.source.lower():
##                        suite_name = os.path.basename(os.environ['output_dir'])
                    if os.path.isfile(self.source) and os.path.exists(self.source):
                        #Eg: directory /var/www/html/sutas-logs/FAS_test_suite2017Aug11_162033_Logs/
                        directory = self.path + suite_name + '_Logs'
                        if 'consolidated' in self.source.lower():
                            directory = self.path
                        try:
                            sftp.stat(directory)
                        except IOError as WindowsError:
                            #Creates directory if not exists
                            sftp.mkdir(directory)
                        global created
                        created = True
                        try:
                            #Example logfile log.html
                            logfile = os.path.basename(self.source)
                            sftp.chdir(directory)
                            url = "/sutas-logs/" + \
                                os.path.basename(directory) + "/" + logfile
                            if 'consolidated' in self.source.lower():
                                url = "/sutas-logs/" + logfile
                            logger.info("Placing Test Artifacts to webserver "
                                        "server at the location:{}".format(url))
                            #put method uploads file to give path
                            sftp.put(self.source, logfile)
                        except Exception as err:
                            logger.warn(err)
                        sftp.close()
                        ssh.close()
                    else:
                        logger.warn('{} File not exists'.format(
                            os.path.basename(self.source)))
        
                    return url
        else:
            msg = "Pushing logs to server is disabled in global_conf file"
            logger.warn(msg, console=False)
            return msg

