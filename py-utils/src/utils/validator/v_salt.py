#!/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import os
from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess


class SaltV:
    """Salt related validations."""

    def validate(self, v_type, args):
        """
        Process salt validations.
        Usage (arguments to be provided):
        1. salt minions <nodes>
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) < 1:
            raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

        if v_type == "minions":
            self.validate_salt_minion_connectivity(args)
        else:
            raise VError(
                errno.EINVAL, "Action parameter %s not supported" % v_type)

    def validate_salt_minion_connectivity(self, nodes):
        """Check salt minion connectivity."""

        if os.environ.get('USER') != 'root':
            res = ("validate_salt_minion: "
                   "This interface requires root privileges.")
            raise VError(errno.EACCES, res)

        for node in nodes:
            cmd = f"salt -t 5 {node} test.ping"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = (f"Salt minion {node} unreachable."
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.ECONNREFUSED, res)
