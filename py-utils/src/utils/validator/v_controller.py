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
import traceback

from cortx.utils.ssh import SSHChannel
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError


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
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if v_type == "accessible":
            if len(args) < 3:
                raise VError(
                    errno.EINVAL, "Insufficient parameters. %s" % args)

            if len(args) > 3:
                raise VError(errno.EINVAL,
                             "Too many parameters '%s' for 'Controller accessible'.\
                                 Refer usage." % args)
            self.validate_controller_accessibility(args[0], args[1], args[2])
        elif v_type == "firmware":
            if len(args) < 4:
                raise VError(
                    errno.EINVAL, "Insufficient parameters. %s" % args)

            if len(args) > 4:
                raise VError(errno.EINVAL,
                             "Too many parameters '%s' for 'Controller firmware'.\
                                 Refer usage." % args)
            self.validate_firmware(args[0], args[1], args[2], args[3])
        else:
            raise VError(
                errno.EINVAL, "Action parameter '{%s}' is not supported.\
                    Refer usage." % v_type)

    def validate_controller_accessibility(self, ip, username, password):
        """Check contoller console is accessible to node."""
        # Check if ssh connection is successful
        try:
            session = SSHChannel(
                host=ip, username=username, password=password)
            session.disconnect()
        except:
            err = traceback.format_exc()
            raise VError(
                errno.EINVAL, "Failed to create ssh connection to %s, Error: %s" % (ip, err))

        # ping controller IP
        cmd = "ping -c 1 -W 1 %s" % ip
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        if rc != 0:
            msg = "Ping failed for IP '%s'. Command: '%s', Return Code: '%s'." % (
                ip, cmd, rc)
            msg += stderr.decode("utf-8").replace('\r', '').replace('\n', '')
            raise VError(errno.EINVAL, msg)

    def validate_firmware(self, ip, username, password, mc_expected):
        """
        Check expected contoller bundle version found
        mc_expected: string or list of expected version(s).
        """
        try:
            session = SSHChannel(
                host=ip, username=username, password=password)
        except:
            err = traceback.format_exc()
            raise VError(
                errno.EINVAL, "Failed to create ssh connection to %s, Error: %s'" % (ip, err))

        # check firmware version command execution on MC
        rc, output = session.execute(self.version_cmd)
        if (rc != 0) or (self.success_msg not in output):
            raise VError(errno.EINVAL,
                         "Controller command failure. Command: %s Output: %s" % (
                             self.version_cmd, output))

        # check expected bundle version is found on MC
        _supported = False
        if mc_expected:
            if isinstance(mc_expected, list):
                _supported = any(ver for ver in mc_expected if ver in output)
            else:
                _supported = True if mc_expected in output else False

        if not _supported:
            raise VError(errno.EINVAL, "Unsupported firmware version found on %s.\
                Expected controller bundle version(s): %s" % (ip, mc_expected))

        session.disconnect()
