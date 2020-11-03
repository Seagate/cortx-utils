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
#import subprocess

from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError


class StorageV:
    """Storage related validations."""

    def validate(self, v_type, args):
        """
        Process storage validations.
        Usage (arguments to be provided):
        1. storage vol_accessible nodes
        2. storage vol_mapped nodes
        3. storage lvm_size nodes
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) < 1:
            raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

        if v_type == "vol_accessible":
            self.validate_volumes_accessible(args)
        elif v_type == "vol_mapped":
            self.validate_volumes_mapped(args)
        elif v_type == "lvm_size":
            self.validate_lvm_equal_sized(args)

        else:
            raise VError(
                errno.EINVAL, "Action parameter %s not supported" % v_type)


    def validate_volumes_accessible(self, nodes):
        """Validate accessible volumes."""

        for node in nodes:
            cmd = f"ssh {node} lsblk -S && ls -1 /dev/disk/by-id/scsi-*"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[2]:
                raise VError(errno.EINVAL, f"Volumes are not accessible at {node}.")

            res = run_result[0].strip()
            print (res)


    def validate_volumes_mapped(self, nodes):
        """Validate mapped volumes."""

        for node in nodes:
            cmd_1 = f"ssh {node} multipath -ll | grep prio=50 | wc -l"
            cmd_2 = f"ssh {node} multipath -ll | grep prio=10 | wc -l"
            cmd_proc_1 = SimpleProcess(cmd_1)
            cmd_proc_2 = SimpleProcess(cmd_2)
            run_result_1 = cmd_proc_1.check_output(shell=True)
            run_result_2 = cmd_proc_2.check_output(shell=True)
            
            if run_result_1[2] or run_result_2[2]:
                raise VError(errno.EINVAL, f"Failed to Get Volumes Mapped for {node}.")

            res1 = run_result_1[0].strip()
            res2 = run_result_2[0].strip()
            print (res1, res2)

            if (int(res1) != 16) or (int(res2) != 16):
                raise VError(errno.EINVAL,
                             f"Volumes Are Not Properly Mapped in {node}.")


    def validate_lvm_equal_sized(self, nodes):
        """Check if LVMs are equal-sized"""

        for node in nodes:
            cmd = ("ssh %s lsscsi -s | grep -e disk | grep -e SEAGATE | awk '{print $7}'" % node)
            #run_result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.check_output(shell=True)
            print ('LVM size', set(run_result[0].splitlines()))

            if run_result[2]:
                raise VError(errno.EINVAL, f"Failed to get LVM details on {node}.")

            res = len(set(run_result[0].splitlines()))
            print (res)

            if int(res) != 1:
                raise VError(errno.EINVAL, f"LVMs Are Not Equal-Sized on {node}.")
