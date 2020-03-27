"""
WINRM Module to connect to windows host
"""
from winrm.protocol import Protocol
from lib import logger


class WINRM(object):
    """
    WINRM Module to connect to windows host
    """
    def __init__(self, host_ip, usr, pwd):
        """
        - **parameters**, **types**, **return** and **return types**::
            :param os_type : windows/linux
            :param host_ip: ip address of the Windows host
            :param usr: username of the Windows Host
            :param pwd: Password of the Windows Host
            :type os_type: string
            :type host_ip: string
            :type u_name: string
            :type pwd: string
        """
        self.os_type = 'windows'
        self.host_ip = host_ip
        self.usr = usr
        self.pwd = pwd
        self.shell_id = None
        self.host_win_ip = None
        self.conn = None

    def connect(self):
        """
            Method to connect to a Windows machine.
        """
        try:
            self.host_win_ip = "http://" + self.host_ip + ":5985/wsman"
            self.conn = Protocol(
                endpoint=self.host_win_ip,
                transport="ntlm",
                username=self.usr,
                password=self.pwd,
                server_cert_validation="ignore")
            logger.warn("Connecting Windows ...")
            self.shell_id = self.conn.open_shell()
            logger.warn(self.shell_id)
            logger.warn('Connected to Windows.')
        except Exception as error:
            msg_exception_error = "Exception raised: %s " % error
            raise(msg_exception_error)

    def run_cmd(self, cmd):
        """
            Generic Method for passing command and run it on windows machine and return output.
             - **parameters**, **types**, **return** and **return types**::
                 :param cmd: Command to be executed on windows machine.
                 :return stdout,stderr,status_code : output,errormessage and statuscode of output.
                 :rtype stdout,stderr,status_code: tuple
        """
        if 'shell_id' in dir(self):
            #checking for the shell_id created in winrm object
            command_id = self.conn.run_command(self.shell_id, cmd)
            std_out, std_err, status_code = self.conn.get_command_output(
                self.shell_id, command_id)
            #runs the command and returns output,error,statuscode
            return std_out, std_err, status_code
