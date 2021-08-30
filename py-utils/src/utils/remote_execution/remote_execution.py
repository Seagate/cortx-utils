#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
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
import paramiko
from cortx.utils.remote_execution import RemoteExecutionError

class RemoteExecution:

    def __init__(self):
        pass

    def node_available(self, node: str):
        """Check if node is available."""
        if node is None:
            raise RemoteExecutionError(errno.EINVAL, "Invalid node value. %s", \
                node)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname='192.168.', username='root',
                    key_filename='/home/ubuntu/.ssh/mykey.pem')

        return 0

    def run(self, node: str, cmd: str, **kwargs):
        """Run commands on remote machines."""
        if node is None:
            raise RemoteExecutionError(errno.EINVAL, "Invalid node value. %s", \
                node)

        if cmd is None:
            raise RemoteExecutionError(errno.EINVAL, "No command provided. %s", \
                node)