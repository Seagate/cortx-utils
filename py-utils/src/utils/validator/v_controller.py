#!/bin/env python3

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

import errno
import socket
import paramiko

from cortx.utils import const
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError
from cortx.utils.security.cipher import Cipher


class ControllerV:
    """Controller related validations."""

    def __init__(self):
        self.mc_supported = []

    def __establish_ssh_connection(self, ip, user, passwd, port=22):
        """Create ssh connection to storage enclosure"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(ip, port, user, passwd, timeout=60)
        except socket.timeout:
            raise VError(errno.EINVAL, "Timedout. Failed to connect '%s' in 60 seconds." % ip)
        except paramiko.ssh_exception.AuthenticationException:
            raise VError(errno.EINVAL, "Invalid username or password. \
                SSH authentication failed with username/password: '%s/%s'" % (user, passwd))
        except Exception as connErr:
            raise VError(errno.EINVAL, "Failed to establish SSH connection to '%s'. Error '%s'"\
                 % (ip, str(connErr)))
        return client

    def __get_bundle_info(self, conn):
        """Validate MC is accessible
        """
        version_cmd = "show versions"
        success_msg = "Command completed successfully"

        # check version command execution on MC
        stdin, stdout, stderr = conn.exec_command(version_cmd)
        response = stdout.read().decode()
        if success_msg not in response:
            raise VError(
                errno.EINVAL, f"Failed to execute command on controller: {version_cmd}")
        return response

    def validate(self, v_type, args):
        """
        Process controller validations.
        Usage (arguments to be provided):
        1. controller accessible <ip> <username> <password>
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, f"Invalid parameters {args}")

        if len(args) < 3:
            raise VError(errno.EINVAL, f"Insufficient parameters. {args}")
        elif len(args) > 3:
            raise VError(errno.EINVAL,
                    f"Too many parameters '{args}' for 'Controller Validator'. Refer usage.")

        if v_type == "accessible":
            self.validate_controller_accessibility(args[0], args[1], args[2])
        else:
            raise VError(
                errno.EINVAL, f"Action parameter '{v_type}' is not supported. Refer usage.")

    def validate_controller_accessibility(self, ip, username, password):
        """Check contoller console is accessible to node
        """
        ssh_conn = self.__establish_ssh_connection(ip, username, password)
        if not ssh_conn:
            raise VError(
                errno.EINVAL, f"Failed to establish connection to controller IP, {ip}")
        bundle_info = self.__get_bundle_info(ssh_conn)

        # check supported bundle version of MC
        _supported = any(ver for ver in self.mc_supported if ver in bundle_info)
        if not _supported:
            raise VError(errno.EINVAL, f"Unsupported bundle version found.\
                Controller Version Info: {bundle_info}")

        ssh_conn.close()
