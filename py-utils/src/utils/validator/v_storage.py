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

from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError


class StorageV:
    """Storage related validations."""

    def validate(self, v_type, args):
        """
        Process storage validations.
        Usage (arguments to be provided):
        1. storage luns nodes
        2. storage lvms nodes
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) < 1:
            raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

        if v_type == "luns":
            self.validate_luns_consistency(args)
        elif v_type == "lvms":
            self.validate_lvm(args)
        else:
            raise VError(
                errno.EINVAL, "Action parameter %s not supported" % v_type)

    def validate_luns_consistency(self, nodes):
        """Validate luns consistency."""

        for node in nodes:
            cmd = f"ssh {node} lsblk -S | grep sas | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = (f"Failed to get luns on {node}."
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)

            res = (run_result[0].decode('utf-8').strip())
            if int(res) == 0 or (int(res) % 16):
                res = (f"The query resulted in {int(res)} number of LUNs"
                       " that are not as per desired configuration on node "
                       f"{node} (which needs to be in multiples of 16 for a "
                       "dual node cluster). To troubleshoot this"
                       " issue execute command: 'lsblk -S | grep sas'")
                raise VError(errno.EINVAL, res)

    def validate_lvm(self, nodes):
        """Validate lvms are present."""

        for node in nodes:

            cmd = f"ssh {node} vgdisplay | grep vg_metadata_{node}"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            if run_result[1] or run_result[2]:
                res = (f"Failed to get vg_metadata_{node} on {node}."
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)

            cmd = f"ssh {node} vgdisplay | grep vg_metadata | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            if run_result[1] or run_result[2]:
                res = (f"Failed to get lvms on {node}."
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)

            res = (run_result[0].decode('utf-8').strip())
            if not res or (int(res) != len(nodes)):
                raise VError(errno.EINVAL,
                             f"No. of Lvms {res} are not correct for {node}.")
