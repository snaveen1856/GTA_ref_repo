"""
SSH Module to connect to Linux Platforms.
"""
import socket
import sys

from six import reraise
from paramiko import client, ssh_exception

CONNECTION_TIMEOUT = 10
SSH_PORT = 22


class NoPasswordAvailable(Exception):
    """
    Class for NoPasswordAvailable
    """
    pass


class SSH(object):

    """SSH connection."""

    def __init__(self, hostname, username=None, password=None,
                 timeout=CONNECTION_TIMEOUT, port=SSH_PORT, sock=None,
                 private_key=None):
        """
        :param hostname: hostname or IP address
        :type hostname: str

        :param password: password
            If no password is specified the client will look for keys in ~/.ssh
            and try to contact an available ssh agent. Only one authentication
            mechanism will be tried, however.
        :type password: str

        :param timeout: connection timeout in seconds
        :type timeout: int
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.port = port
        self.sock = sock
        self.private_key = private_key
        self.client = None

    def connect(self):
        """
        Method to connect to Linux Machine
        """
        self.client = client.SSHClient()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        look_for_keys = allow_agent = self.password is None
        try:
            self.client.connect(
                self.hostname, username=self.username, password=self.password,
                timeout=self.timeout, port=self.port,
                look_for_keys=look_for_keys, allow_agent=allow_agent,
                sock=self.sock, pkey=self.private_key)
        except socket.timeout:
            print(("Connection timed out, unable to contact host: %s"
                   % self.hostname))
            raise
        except ssh_exception.BadAuthenticationType as err:
            error_message = ("Failed to SSH using %s:%s@%s. %s" %
                             (self.username, self.password, self.hostname, err.args[0]))
            exc_info = sys.exc_info()
            reraise(exc_info[0], exc_info[0](
                error_message, err.args[1]), exc_info[2])

    def close(self):
        """Close the connection.

        Any child channels will also be closed.

        """
        if self.client:
            self.client.close()

    def reconnect(self):
        """Reconnect to the host by closing and reopening the connection."""
        self.close()
        self.connect()

    def command_exec(self, command, timeout=CONNECTION_TIMEOUT, sudo=False,
                     sudo_password=None):
        """Execute a command on the host.

        :return: (exit_status, stdout, stderr), where exit_status is an int and
            stdout and stderr are file-like objects. exit_status will be -1 if
            no status is provided by the server.

        """
        bufsize = -1
        if sudo and not (sudo_password or self.password):
            raise NoPasswordAvailable("No password set, provide one to "
                                      "the 'sudo_password' kwarg")
        elif sudo:
            command = 'echo %s | sudo -S %s' % (sudo_password or self.password,
                                                command)
        out, err = self.client.exec_command(command,
                                            bufsize=bufsize,
                                            timeout=timeout)[1:]
        out.channel.recv_exit_status()
        return_code = out.channel.exit_status

        return return_code, out.read(), err

    def check_output(self, command, timeout=None, sudo=False,
                     sudo_password=None):
        """Execute a command on the host and return its output.

        If the return code is a non-zero, ExecutionError will be raised.

        """
        return_code, stdout, stderr = (
            self.client.exec_command(command, timeout=timeout, sudo=sudo,
                                     sudo_password=sudo_password))
        stdout_contents = stdout.read()
        if return_code:
            stderr_contents = stderr.read()
            raise Exception(stderr_contents)
        return stdout_contents
