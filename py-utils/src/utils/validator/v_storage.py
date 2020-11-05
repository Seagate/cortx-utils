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
        1. storage rpm rpm_name nodes
        2. storage hca nodes
        3. storage hca_ports nodes
        4. storage lsb_hba nodes
        5. storage lsb_hba_ports nodes
        6. storage luns nodes
        7. storage lvms nodes
        8. storage volumes nodes
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if v_type == "rpm":
            if len(args) < 2:
                raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)
            else:
                self.validate_rpm(args[0], args[1:])

        else:
            if len(args) < 1:
                raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

            if v_type == "hca":
                self.validate_mlnx_hca_present(args)
            elif v_type == "hca_ports":
                self.validate_mlnx_hca_req_ports(args)
            elif v_type == "lsb_hba":
                self.validate_lsb_hba_present(args)
            elif v_type == "lsb_hba_ports":
                self.validate_lsb_hba_req_ports(args)

            elif v_type == "luns":
                self.validate_luns_consistency(args)
            elif v_type == "lvms":
                self.validate_lvm(args)
            elif v_type == "volumes":
                self.validate_volumes_mapped(args)

            else:
                raise VError(
                    errno.EINVAL, "Action parameter %s not supported" % v_type)


    def validate_rpm(self, rpm, nodes):
        """Check if given RPM (eg: Mellanox OFED) is Installed"""

        for node in nodes:
           cmd = f"ssh {node} rpm -qa | grep {rpm}"
           cmd_proc = SimpleProcess(cmd)
           run_result = cmd_proc.run()

           if run_result[1] or run_result[2]:
               res = (f"Given RPM '{rpm}' Is Not Installed on {node}. "
                      f"Also, check if '{node}' is valid. "
                      f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
               raise VError(errno.EINVAL, res)

           #res = run_result[0].strip()


    def validate_mlnx_hca_present(self, nodes):
        """Check if Mellanox HCA is present"""

        for node in nodes:
            cmd = f"ssh {node} lspci -nn | grep 'Mellanox Technologies'"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = ("Mellanox Host Channel Adapters card "
                       f"possibly with Infiniband capability) is not detected on {node}. "
                       f"Also, check if '{node}' is valid. "
                       f"CMD '{cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)


    def validate_mlnx_hca_req_ports(self, nodes):
        """Check if Mellanox HCA has Req Ports"""

        for node in nodes:
            cmd = f"ssh {node} lspci -nn | grep 'Mellanox Technologies' | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = ("Mellanox Host Channel Adapters ports were not "
                       "detected by command 'lspci -nn | grep 'Mellanox Technologies'. "
                       f"Also, check if '{node}' is valid. ")
                raise VError(errno.EINVAL, res)

            res = (run_result[0].decode('utf-8').strip())
            if int(res) == 0:
                res = ("Mellanox Host Channel Adapters ports were not "
                       "detected by command 'lspci -nn | grep 'Mellanox Technologies'. "
                       "For high-speed data network, it is expected to "
                       "have at least one port present over some PCIe slot. ")
                raise VError(errno.EINVAL, res)


    def validate_lsb_hba_present(self, nodes):
        """Check if HBA is present"""

        for node in nodes:
            cmd = f"ssh {node} lspci -nn | grep 'SCSI'"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = ("Host Bus Adapters (HBA) for "
                       f"SAS channels not detected on {node}. "
                       f"Also, check if '{node}' is valid. "
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)


    def validate_lsb_hba_req_ports(self, nodes):
        """Check if LSB HBA has Req Ports"""

        for node in nodes:
            cmd = f"ssh {node} ls /sys/class/scsi_host/ | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = ("Host Bus Adapters (HBA) for "
                       f"SAS channels not detected on {node}. "
                       f"Also, check if '{node}' is valid. ")
                raise VError(errno.EINVAL, res)

            res = run_result[0].decode('utf-8').strip()
            if int(res) == 0:
                res = ("Host Bus Adapters (HBA) for "
                       f"SAS channels not detected on {node}. "
                       "For storage connectivity over SAS channels "
                       "to JBOD/RBOD there is expectation for a PCIe HBA card "
                       "to be present. Please check HW, if this system "
                       "expects a connection to either JBOD or RBOD." )
                raise VError(errno.EINVAL, res)


    def validate_luns_consistency(self, nodes):
        """Validate luns consistency."""

        for node in nodes:
            cmd = f"ssh {node} lsblk -S | grep sas | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = (f"Failed to get luns on {node}. "
                       f"Also, check if '{node}' is valid. "
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

            cmd = ("ssh %s lsscsi -s | grep -e disk | grep -e SEAGATE | awk '{print $7}'" % node)
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            print (f"LUN size on {node}:", set(run_result[0].decode('utf-8').splitlines()))

            if run_result[1] or run_result[2]:
                res = (f"Failed to get lvms on {node}. "
                       f"Also, check if '{node}' is valid. "
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)

            res = len(set(run_result[0].splitlines()))

            if int(res) != 1:
                raise VError(errno.EINVAL, f"LUNs Are Not Equal-Sized on {node}.")


    def validate_lvm(self, nodes):
        """Validate lvms are present and size."""

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
                             f"No. of Lvms {res} is not correct for {node}.")


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
