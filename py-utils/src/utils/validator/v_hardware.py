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

from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess
from cortx.utils.const import ITEMS_SEPARATOR


class HardwareV:
    """Hardware related validations."""

    def validate(self, v_type, args):
        """
        Hardware Pre-Deployment validations.
        Usage (arguments not needed):
        1. hardware rpm rpm_name nodes
        2. hardware hca nodes
        3. hardware hca_ports nodes
        4. hardware hba nodes
        5. hardware hba_ports nodes
        
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if v_type == "rpm":
            print ("Input Args .. ", args)
            if len(args) < 2:
                raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)
            else:
                self.validate_rpm(args[0], args[1:])
        
        else:
            print ("Input Args .. ", args)
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
            else:
                raise VError(
                    errno.EINVAL, "Action parameter %s not supported" % args[0])


    def validate_rpm(self, rpm, nodes):
        """Check if given RPM (eg: Mellanox OFED) is Installed"""

        for node in nodes:
            cmd = f"ssh {node} rpm -qa | grep {rpm}"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            if run_result[2]:
                raise VError(errno.EINVAL, f"{rpm} Not Installed on {node}.")
            res = run_result[0].strip()
            print (res)


    def validate_mlnx_hca_present(self, nodes):
        """Check if Mellanox HCA is present"""

        for node in nodes:
            cmd = f"ssh {node} lspci -nn | grep 'Mellanox Technologies'"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            if run_result[2]:
                raise VError(errno.EINVAL, f"HCA Not Present on {node}.")

            res = run_result[0].strip()
            print (res)


    def validate_mlnx_hca_req_ports(self, nodes):
        """Check if Mellanox HCA has Req Ports"""

        for node in nodes:
            cmd = f"ssh {node} lspci -nn | grep 'Mellanox Technologies' | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.check_output(shell=True)
            
            if run_result[2]:
                raise VError(run_result[2], run_result[1])

            res = run_result[0].strip()
            print (res)
            if int(res) == 0:
                raise VError(errno.EINVAL, f"HCA Does Not Have Req Ports on {node}.")


    def validate_lsb_hba_present(self, nodes):
        """Check if Mellanox HBA is present"""

        for node in nodes:
            cmd = f"ssh {node} lspci -nn | grep 'SCSI'"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            if run_result[2]:
                raise VError(errno.EINVAL, f"HBA Not Present on {node}.")

            res = run_result[0].strip()
            print (res)


    def validate_lsb_hba_req_ports(self, nodes):
        """Check if LSB HBA has Req Ports"""

        for node in nodes:
            cmd = f"ssh {node} ls /sys/class/scsi_host/ | wc -l"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.check_output(shell=True)
            
            if run_result[2]:
                raise VError(run_result[2], run_result[1])

            res = run_result[0].strip()
            print (res)
            if int(res) == 0:
                raise VError(errno.EINVAL, f"HBA Does Not Have Req Ports on {node}.")
