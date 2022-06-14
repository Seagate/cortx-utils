#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import socket
import getpass
import paramiko
import traceback

from cortx.utils.log import Log
from cortx.utils.comm import Channel


class SSHChannel(Channel):
    """Establish SSH connection on remote host"""

    def __init__(self, host, username=None, password=None, port=22, pkey_filename=None, allow_agent=False, **args):
        super().__init__()
        self.host = host
        self.__user = username or getpass.getuser()
        self.__pwd = password
        self.port = port
        self.pkey_filename = pkey_filename
        self.allow_agent = allow_agent
        self.timeout = 30
        self.client = None
        self.sftp_enabled = False
        self.__sftp = None
        for key, value in args.items():
            setattr(self, key, value)
        self.connect()

    def init(self):
        raise Exception('init not implemented for SSH Channel')

    def connect(self):
        """Creates ssh connection
           Also helps to reconnect same client without invoking new
           instance again if diconnect caller on the client is called
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host,
                                port=self.port,
                                username=self.__user,
                                password=self.__pwd,
                                allow_agent=self.allow_agent,
                                key_filename=self.pkey_filename,
                                timeout=self.timeout)
            if self.sftp_enabled:
                self.__sftp = self.client.open_sftp()
        except paramiko.AuthenticationException:
            raise Exception("Authentication failed, verify your credentials.")
        except paramiko.SSHException:
            sshError = traceback.format_exc()
            raise Exception(f"Could not establish SSH connection. {sshError}")
        except socket.timeout:
            raise Exception(f"Timedout. Failed to connect {self.host} in {self.timeout} seconds")
        except:
            sshError = traceback.format_exc()
            raise Exception(f"Exception in connecting to {self.host}\n. {sshError}")

    def execute(self, command):
        """Execute command on remote host
        """
        if not self.is_connection_alive:
            self.connect()
        _, stdout, stderr = self.client.exec_command(command)
        rc = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        if rc != 0: output = error
        return rc, output

    def send(self, message):
        raise Exception('send not implemented for SSH Channel')

    def recv(self, message=None):
        raise Exception('recv not implemented for SSH Channel')

    def recv_file(self, remote_file, local_file):
        """ Get a file from node """
        if not self.sftp_enabled:
            raise Exception('Internal Error: SFTP is not enabled')
        try:
            self.__sftp.get(remote_file, local_file)
        except Exception as e:
            raise Exception(e)

    def send_file(self, local_file, remote_file):
        """ Put a file in node """
        if not self.sftp_enabled:
            raise Exception('Internal Error: SFTP is not enabled')
        try:
            self.__sftp.put(local_file, remote_file)
        except Exception as e:
            raise Exception(e)

    def acknowledge(self, delivery_tag=None):
        raise Exception('acknowledge not implemented for SSH Channel')

    def is_connection_alive(self):
        """Check transporting tunnel is active
        """
        if (self.client is None) or (self.client.get_transport() is None):
            return False
        return True

    def disconnect(self):
        """Close the created ssh connection
        """
        if self.client:
            try:
                # Failure due to this may leave transport tunnel opened.
                if self.sftp_enabled: self.__sftp.close()
                self.client.close()
            except Exception as e:
                Log.exception(e)
        # Explicitly handling the client connection
        # instead of relying on garbage collection
        self.client = None

    def __del__(self):
        """Destruct the connection
        """
        self.disconnect()
