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

from cortx.utils import const
from cortx.utils.comm import SSHSession
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError
from cortx.utils.security.cipher import Cipher


class ControllerV:
    """Controller related validations."""

    def __init__(self):
        self.version_cmd = "show versions"
        self.success_msg = "Command completed successfully"

    def validate(self, v_type, args):
        """
        Process controller validations.
        Usage (arguments to be provided):
        1. controller accessible <ip> <username> <password>
        2. controller firmware <ip> <username> <password> <mc_version>
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, f"Invalid parameters {args}")

        if v_type == "accessible":
            if len(args) < 3:
                raise VError(errno.EINVAL, f"Insufficient parameters. {args}")

            if len(args) > 3:
                raise VError(errno.EINVAL,
                        f"Too many parameters '{args}' for 'Controller accessible'. Refer usage.")
            self.validate_controller_accessibility(args[0], args[1], args[2])
        elif v_type == "firmware":
            if len(args) < 4:
                raise VError(errno.EINVAL, f"Insufficient parameters. {args}")

            if len(args) > 4:
                raise VError(errno.EINVAL,
                        f"Too many parameters '{args}' for 'Controller firmware'. Refer usage.")
            self.validate_firmware(args[0], args[1], args[2], args[3])
        else:
            raise VError(
                errno.EINVAL, f"Action parameter '{v_type}' is not supported. Refer usage.")

    def validate_controller_accessibility(self, ip, username, password):
        """Check contoller console is accessible to node
        """
        # Check if ssh connection is successful
        session = SSHSession(host=ip, username=username, password=password)
        session.disconnect()

        # ping controller IP
        cmd = f"ping -c 1 -W 1 {ip}"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        if rc != 0:
            msg = f"Ping failed for IP '{ip}'. Command: '{cmd}', Return Code: '{rc}'."
            msg += stderr.decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)

    def validate_firmware(self, ip, username, password, mc_expected):
        """Check expected contoller bundle version found
            mc_expected: string or list of expected version(s)
        """
        session = SSHSession(host=ip, username=username, password=password)

        # check firmware version command execution on MC
        stdin, stdout, stderr = session.exec_command(self.version_cmd)
        cmd_output = stdout.read().decode()
        cmd_error = stderr.read().decode()
        if self.success_msg not in cmd_output:
            raise VError(
                errno.EINVAL, f"Command failure on controller, '{self.version_cmd}'")

        # check expected bundle version is found on MC
        _supported = False
        if mc_expected:
            if type(mc_expected, list):
                _supported = any(ver for ver in mc_expected if ver in cmd_output)
            else:
                _supported = True if mc_expected in cmd_output else False

        if not _supported:
            raise VError(errno.EINVAL, f"Unsupported firmware version found on {ip}.\
                Expected controller bundle version(s): {mc_expected}")

        session.disconnect()
