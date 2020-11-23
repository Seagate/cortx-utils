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

import os
import socket
import paramiko
import traceback


class SSHSession:
    """Establish SSH connection on remote host"""

    def __init__(self, host, username, password=None, port=22, use_pkey=False):
        self.host = host
        self.__user = username
        self.__pwd = password
        self.port = port
        self.use_pkey = use_pkey
        self.timeout = 30
        self.client = None
        self.connect()

    def connect(self):
        """Creates ssh connection
           Also helps to reconnect same client without invoking new
           instance again if diconnect caller on the client is called
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.use_pkey:
                pkey_file = os.path.expanduser('~/.ssh/id_rsa_prvsnr')
                key = paramiko.RSAKey.from_private_key_file(pkey_file)
                self.client.connect(hostname=self.host,
                                    port=self.port,
                                    username=self.__user,
                                    pkey=key,
                                    timeout=self.timeout)
            else:
                self.client.connect(hostname=self.host,
                                    port=self.port,
                                    username=self.__user,
                                    password=self.__pwd,
                                    timeout=self.timeout)
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

    def exec_command(self, command):
        """Execute command on remote host
        """
        if not self.is_connection_alive:
            self.connect()
        stdin, stdout, stderr = self.client.exec_command(command)
        return (stdin, stdout, stderr)

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
                self.client.close()
            except:
                pass
        # Explicitly handling the client connection
        # instead of relying on garbage collection
        self.client = None

    def __del__(self):
        """Destruct the connection
        """
        self.disconnect()
