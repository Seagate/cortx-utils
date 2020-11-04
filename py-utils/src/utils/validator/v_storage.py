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
        3. storage luns_accessible nodes
        4. storage volumes_mapped nodes
        5. storage lvm_size nodes
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) < 1:
            raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

        if v_type == "luns":
            self.validate_luns_consistency(args)
        elif v_type == "lvms":
            self.validate_lvm(args)
        elif v_type == "luns_accessible":
            self.validate_volumes_accessible(args)
        elif v_type == "volumes_mapped":
            self.validate_volumes_mapped(args)
        elif v_type == "lvm_size":
            self.validate_lvm_equal_sized(args)
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


    def validate_luns_accessible(self, nodes):
        """Validate accessible luns."""

        for node in nodes:
            cmd = f"ssh {node} lsblk -S && ls -1 /dev/disk/by-id/scsi-*"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = ("LUNs from Direct Attached Storage (DAS) are "
                       f"not accessible/available on server {node}. "
                       f"Also, check if '{node}' is valid. "
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)


    def validate_volumes_mapped(self, nodes):
        """Validate mapped volumes."""

        for node in nodes:
            cmd_1 = f"ssh {node} multipath -ll | grep prio=50 | wc -l"
            cmd_2 = f"ssh {node} multipath -ll | grep prio=10 | wc -l"
            cmd_proc_1 = SimpleProcess(cmd_1)
            cmd_proc_2 = SimpleProcess(cmd_2)
            run_result_1 = cmd_proc_1.run()
            run_result_2 = cmd_proc_2.run()

            if (run_result_1[1] or run_result_1[2] or
                run_result_2[1] or run_result_2[2]):
                res = ("Failed to detect volumes from Direct Attached Storage (DAS) "
                       f"(available as LUNs) mapped for server {node}. "
                       f"Also, check if '{node}' is valid. "
                       "Commands 'multipath -ll | grep prio=50 | wc -l' "
                       "and 'multipath -ll | grep prio=10 | wc -l' failed. "
                       f"{run_result_1[0]}. {run_result_1[1]} "
                       f"{run_result_2[0]}. {run_result_2[1]}")
                raise VError(errno.EINVAL, res)

            res1 = (run_result_1[0].decode('utf-8').strip())
            res2 = (run_result_2[0].decode('utf-8').strip())
            print (res1, res2)

            if (int(res1) != 16) or (int(res2) != 16):
                res = ("Volumes from Direct Attached Storage (DAS) are "
                       f"not properly mapped in multipath service for {node}. "
                       "It is expected to detect LUNs in multiples for 16. "
                       "Troubleshoot the issue and execute the following "
                       "command on each node: 'multipath -ll | grep prio=50 | wc -l'")
                raise VError(errno.EINVAL, res)


    def validate_lvm_equal_sized(self, nodes):
        """Check if LVMs are equal-sized"""

        for node in nodes:
            cmd = ("ssh %s lsscsi -s | grep -e disk | grep -e SEAGATE | awk '{print $7}'" % node)
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            print ('LVM size', set(run_result[0].decode('utf-8').splitlines()))

            if run_result[1] or run_result[2]:
                res = (f"Failed to get lvms on {node}. "
                       f"Also, check if '{node}' is valid. "
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)

            res = len(set(run_result[0].splitlines()))

            if int(res) != 1:
                raise VError(errno.EINVAL, f"LVMs Are Not Equal-Sized on {node}.")
