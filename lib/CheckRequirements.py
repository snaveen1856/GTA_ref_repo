"""
Checks the requirements of the test cases if defined in the first step of test case.
Checks for both hardware and software requirements.
"""
from os.path import expanduser
from lib.SSH import SSH
from lib.IntConfig import notify
from lib.utilities import get_data_from_yaml
from lib import logger
from robot.libraries.BuiltIn import BuiltIn
from winrm.protocol import Protocol
import sys, traceback, paramiko
import os,re
import yaml
import requests
import warnings
warnings.filterwarnings('ignore')

class CheckRequirements(object):
    """
    Validates pre-requisite requirements before executing test cases
    """
    def __init__(self):
        """
        Map each software with the command to find the existence of
        the software in each device.

        """
        win_find = 'net start | find \"Microsoft iSCSI Initiator Service\"'
        lin_find = 'find /etc/* -type f -name "initiatorname.iscsi"'
        lin_vdbench = 'find / -type f -name "vdbench"'
        licence = 'system license show'
        self.software_mapping = {
            "Netapp": {'licenses':licence},
            "Linux": {
                     'vdbench' : lin_vdbench,
                     'iscsi' : lin_find
                     },
            "Windows":{
                      'vdbench' : 'where /R c:\ vdbench.bat',
                      'iscsi' : win_find,
                      'iometer' : 'where /R c:\ iometer.exe',
                      'mpio' : "powershell -command "
                      "\"&{&'Import-Module' Servermanager}"
                               ";\" \"&{&'Get-WindowsFeature' -Name"
                               " \"Multipath*\"| Where-Object"
                               " {$_.Installed -match $True}}\" "
            }
        }
        self.tcname = None
        self.globalfilepath = os.path.join(expanduser('~'), "global_conf.yaml")

    def validate_hitachi_software(self, ip, u_name, pwd, model,
                                  serial_number, port, licenses, tcname):
        """
        Connects to Hitachi host and checks for License existence

        - **parameters**, **types**, **return** and **return types**::

            :param host_ip: Hitachi array IP
            :param u_name:  Hitachi array username
            :param p_word:  Hitachi array Password
            :param softwares: List of software to be checked
            :type host_ip: string
            :type u_name: string
            :type p_word: string
            :type softwares: List
            :return: Returns None
        """
        base_URL = "https://"+ip+":"+str(port)+"/ConfigurationManager"+\
                   "/v1/objects/storages/"
        try:
            logger.info('*** Connecting to Hitachi Array...')
            resp = requests.get(base_URL,auth=(u_name,pwd),verify = False)
            data=resp.json()
            for array in data['data']:
                if array['model'] == model and \
                   array['serialNumber'] == int(serial_number):
                    sdid = array['storageDeviceId'] 
                    logger.info('connection  to Hitachi successfull,'
                                'Hence starting test case execution.')
                    url = base_URL + sdid + '/' + 'licenses'
                    resp = requests.get(url,auth=(u_name,pwd),verify = False)
                    out = resp.json()
                    for dev in out['data']:
                        for pro in licenses:
                            if dev['programProductName'] == pro:
                                if dev['status'] == 'Installed':
                                    msg = "Required Software {} is installed".format(pro)
                                    logger.info(msg)
                                else:
                                    msg = ('Required software {} is {}.Hence Skipping the '
                                            'Test case {}...'.format(pro,dev['status'],tcname))
                                    raise Exception(msg)
                else:
                    msg = "Provided Hitachi model is not registered with "\
                          "rest server / Management server"
                    logger.error(msg)
                    raise Exception(msg)

        except Exception as err:
            notify.message(str(err))
            logger.error(err)
            raise Exception(err)

    def validate_netapp_software(self, url, u_name, pwd, netapp_ip,
                                 netapp_username, netapp_password,
                                 array_name, licenses, tcname):
        """
        Connects to Netapp host and checks for License existence

        - **parameters**, **types**, **return** and **return types**::

            :param host_ip: Netapp array IP
            :param u_name:  Netapp array username
            :param p_word:  Netapp array Password
            :param  softwares: List of software to be checked
            :type host_ip: string
            :type u_name: string
            :type p_word: string
            :type softwares: list

            TODO: license check is pending because of rest api unavailability.
        """
        try:
            burl=url+'/api/1.0/admin/storage-systems'
            logger.info('*** Connecting to Netapp Rest Server...')
            resp=requests.get(burl,auth=(u_name,pwd),verify=False)
            data=resp.json()
            if 'result' in data:
                if 'records' in data['result']:
                    for record in data['result']['records']:
                        if record['name']==array_name and \
                            record['ipv4_address']==netapp_ip:
                            logger.info(array_name +" is available "
                                        "in Netapp OCSM")

                            break
                        else:
                            msg = "Netapp is not registered "\
                                "with provided rest server Management server"
                            logger.error(msg)
                            raise Exception(msg)
        except Exception:
            msg = "Unable to connect Netapp... Hardware requirement failed."\
                "Hence Skipping the Test case {}..." .format(tcname)
            notify.message(msg)
            logger.error(msg, console=False)
            raise Exception(msg)
        try:
            logger.info('*** Connecting to Netapp Array...')
            conn = SSH(netapp_ip, netapp_username, netapp_password)
            conn.connect()
        except Exception:
            logger.error('Unable to ssh. Check the connectivity, ip and credentials.')
            raise Exception('Unable to Connect to FAS.Hardware Validation Failed.Hence Skipping the Test case {}...' )
        returncode, stdout, stderr = conn.command_exec('system license show')
        logger.info(stdout)
        if returncode:
            logger.error(stdout)
            raise Exception(stdout)
        for licen in licenses:
            lic_found = re.search(licen,stdout,re.IGNORECASE)
            if lic_found is not None:
                msg = '%s license is available'%licen
                logger.info(msg)
            else:
                msg = '{} licence is not available,Software validation failed.Hence Skipping the Test case {}...'.format(licen,tcname)
                logger.error(msg)
                raise Exception(msg)
        conn.close()

    def get_rqmt(self, kwargs):
        """
        Get the requirements dictionary from each test case

        - **parameters**, **types**, **return** and **return types**::

            :param kwargs: Dictionary with devices as keys and softwares as values
            :type kwargs: Dict
        """
        self.tcname = BuiltIn().get_variable_value("${TEST NAME}")
        msg = ("\n\nValidating Software/Hardware requirements (%s) for "
               "test case %s\n " %(kwargs, self.tcname))
        logger.info(msg)
        notify.message(msg)
        sw_dict = kwargs
        configfile = os.environ['Configfile']
        data = get_data_from_yaml(configfile)
        for device in sw_dict:
            try:
                softwares = sw_dict[device].split(",")
                check = [True for i in ["RHEL".lower(), "Windows".lower(),"Switch".lower()] if i in device.lower()]
                if check:
                    device_ip = data[str(device)]['ip']
                    device_user = data[str(device)]['username']
                    device_pswd = data[str(device)]['password']
                    if device_ip and device_user and device_pswd:
                        if device.startswith("RHEL"):
                            self.connectLinux(device_ip, device_user,
                                              device_pswd, softwares,
                                              self.tcname)
                        elif device.startswith("Windows"):
                            self.connectWin(device_ip, device_user,
                                            device_pswd, softwares, self.tcname)
                        elif device.startswith("Switch"):
                            self.connectSwitch(device_ip, device_user,
                                               device_pswd, self.tcname)
                elif device.lower().startswith("hitachi"):
                    ip = data[device]['rest_ip']
                    u_name = data[device]['rest_username']
                    pwd = data[device]['rest_password']
                    model= data[device]['model']
                    serial_number = data[device]['serial_number']
                    port = data[device]['rest_port']
                    self.validate_hitachi_software(ip, u_name, pwd, model,
                                        serial_number, port, softwares, self.tcname)
                elif device.lower().startswith("netapp"):
                    ip = data[device]['rest_ip']
                    u_name = data[device]['rest_username']
                    pwd = data[device]['rest_password']
                    netapp_ip = data[device]['netapp_ip']
                    netapp_username = data[device]['netapp_username']
                    netapp_password = data[device]['netapp_password']
                    array_name = data[device]['array_name']
                    self.validate_netapp_software(ip, u_name, pwd, netapp_ip, netapp_username, netapp_password,
                                       array_name, softwares, self.tcname)
            except KeyError as e:
                text = "Device {}, connection info missing in config file" \
                    "so, software cannot be checked for this device." \
                       "Hence skipping the Test case {} " .format(device,
                                                                  self.tcname)
                logger.error(text)
                notify.message(text)
                raise Exception(e)
            except Exception as e:
                logger.error(str(e))
                notify.message(str(e))
                raise Exception(e)

    def getSoftwareCmd(self, software, os):
        """
        Get command mapped to the given software

        - **parameters**, **types**, **return** and **return types**::

            :param software: name of the software to be verified
            :param os: name of the OS i.e RHEL or Windows.
            :type software: string
            :type os: string
        """
        return self.software_mapping[os][software]

    def connectLinux(self, host_ip, u_name, p_word, softwares, tcname):
        """
        Connects to Linux host and checks for software existence

        - **parameters**, **types**, **return** and **return types**::

            :param host_ip: Linux host IP
            :param u_name: Linux host username
            :param p_word: Linux host Password
            :param softwares: List of software to be checked
            :type host_ip: string
            :type u_name: string
            :type p_word: string
            :type softwares: list

        """
        try:
            logger.info('*** Connecting to linux box...')
            conn = SSH(host_ip, u_name, p_word)
            conn.connect()
        except Exception:
            text = 'Unable to connect Linux Host...'\
                      'Hardware requirement failed.'\
                      'Hence Skipping the Test case {}...' .format(tcname)
            logger.error(text)
            notify.message(text)
            raise Exception(text)
        try:
            for software in softwares:
                logger.info('Checking for software {} ...' .format(software))
                returncode, stdout, stderr = conn.command_exec(
                                            self.getSoftwareCmd(software,
                                                                "Linux"))
                if not stdout:
                    msg = "Software {} does not exist. " \
                      "Hence Skipping the test case {}..." .format(software,
                                                                   tcname)
                    notify.message(msg)
                    raise Exception(msg)
                msg = 'Found software on host %s at ' %host_ip + stdout
                logger.info(msg)

        except Exception:
            text = '{} not found on Linux Host...'\
                  'software requirement failed.'\
                  'Hence Skipping the Test case {}...' .format(software, tcname)
            logger.error(text)
            notify.message(text)
            raise Exception(text)
        conn.close()

    def connectWin(self, host_ip, u_name, p_word, softwares, tc_name):
        """
        Connects to Windows Host and checks for software existence

            - **parameters**, **types**, **return** and **return types**::

            :param host_ip: windows host ip
            :param u_name: windows host username
            :param p_word: windows host password
            :param softwares: list of softwares to be checked
            :type host_ip: string
            :type u_name: string
            :type p_word: string
            :type softwares: list
        """
        hostIP = "http://" + host_ip + ":5985/wsman"
        try:
            pro = Protocol(
                endpoint=hostIP,
                transport='ntlm',
                username=u_name,
                password=p_word,
                server_cert_validation='ignore')
            logger.info("\n***Connecting  to Windows Host...")
            shell_id = pro.open_shell()
            for software in softwares:
                logger.info("Checking for software {} in "\
                            "windows" .format(software))
                command_id = pro.run_command(shell_id,
                                             self.getSoftwareCmd(software,
                                                                 "Windows")
                                             )
                std_out, std_err, status_code = pro.get_command_output(
                    shell_id, command_id)
                msg = "Software {} does not exist in the C drive.."\
                    "Hence Skipping"\
                      "the test case {}..." .format(software, tc_name)
                if std_out == "":
                    notify.message(msg)
                    raise Exception(msg)
                msg = 'Found software on host %s at ' %host_ip + std_out
                logger.info(msg)
                pro.cleanup_command(shell_id, command_id)
            pro.close_shell(shell_id)
        except Exception as e:
            text = "Requirements pre check failed.. "\
                "Hence Skipping the test case "\
               "{} ..." .format(tc_name)
            logger.error(text)
            notify.message(text)
            raise Exception(text)

    def connectSwitch(self, host_ip, u_name, p_word, tc_name):
        """
        Connects to Linux host and checks for software existence

            - **parameters**, **types**, **return** and **return types**::

                :param host_ip: Linux host IP
                :param u_name: Linux host username
                :param p_word: Linux host Password
                :param softwares: List of software to be checked
                :type host_ip: string
                :type u_name: string
                :type p_word: string
                :type softwares: list
        """
        port = 22
        client = paramiko.SSHClient()
        try:
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.info('*** Connecting to Switch...')
            client.connect(host_ip, port, u_name, p_word)
            stdin, stdout, stderr = client.exec_command('version')
            client.close()
        except Exception:
            msg = "Unable to connect Switch..Hardware requirement failed" \
                  "Hence skipping test case {}".format(tc_name)
            logger.error(msg)
            notify.message(msg)
            raise Exception(msg)
