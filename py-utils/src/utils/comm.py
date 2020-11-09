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
import paramiko
import traceback
from abc import ABCMeta, abstractmethod

class Channel(metaclass=ABCMeta):

    """Abstract class to represent a comm channel to a node"""

    @abstractmethod
    def init(self):
        raise Exception('init not implemented in Channel class')

    @abstractmethod
    def connect(self):
        raise Exception('connect not implemented in Channel class')

    @abstractmethod
    def disconnect(self):
        raise Exception('disconnect not implemented in Channel class')

    @abstractmethod
    def send(self, message):
        raise Exception('send not implemented in Channel class')

    @abstractmethod
    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented in Channel class')

    @abstractmethod
    def recv(self, message=None):
        raise Exception('recv not implemented in Channel class')

    @abstractmethod
    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented in Channel class')

    @abstractmethod
    def acknowledge(self, delivery_tag=None):
        raise Exception('acknowledge not implemented for Channel class')


class Comm(metaclass=ABCMeta):

    """Abstract class to represent a comm channel"""

    @abstractmethod
    def init(self):
        raise Exception('init not implemented in Comm class')

    @abstractmethod
    def connect(self):
        raise Exception('connect not implemented in Comm class')

    @abstractmethod
    def disconnect(self):
        raise Exception('disconnect not implemented in Comm class')

    @abstractmethod
    def send(self, message, **kwargs):
        raise Exception('send not implemented in Comm class')

    @abstractmethod
    def send_message_list(self, message: list, **kwargs):
        raise Exception('send_message_list not implemented in Comm class')

    @abstractmethod
    def recv(self, callback_fn=None, message=None, **kwargs):
        raise Exception('recv not implemented in Comm class')

    @abstractmethod
    def acknowledge(self):
        raise Exception('acknowledge not implemented in Comm class')


class SSHSession:

    """Establish SSH connection on remote host"""

    def __init__(self, host, username, password):
        self.host = host
        self.user = username
        self.pwd = password
        self.port = 22
        self.timeout = 30
        self.client = None
        self.__connect()

    def __connect(self):
        """create ssh connection
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host,
                                port=self.port,
                                username=self.user,
                                password=self.pwd,
                                timeout=self.timeout)
        #except paramiko.ssh_exception.AuthenticationException:
        except paramiko.AuthenticationException:
            raise Exception(f"Authentication failed, verify your credentials.")
        except paramiko.SSHException:
            sshError = traceback.format_exc()
            raise Exception(f"Could not establish SSH connection. {sshError}")
        except socket.timeout:
            raise Exception(f"Timedout. Failed to connect {self.host} in {self.timeout} seconds")
        except:
            sshError = traceback.format_exc()
            raise Exception(f"Exception in connecting to {self.host}\n. {sshError}")

    def exec_command(self, command):
        """Execute command on remote host
        """
        if self.client is None:
            self.client == self.__connect()
        stdin, stdout, stderr = self.client.exec_command(command)
        return (stdin, stdout, stderr)

    def disconnect(self):
        """Close the created ssh connection
        """
        self.client.close()
