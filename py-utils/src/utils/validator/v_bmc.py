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

from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess


class BmcV:
    """BMC related validations."""

    def __init__(self):
        self.channel_cmd = "channel info"

    def __get_bmc_ip(self, node):
        """ Get BMC IP along with status of command
        """

        cmd = f"ssh {node} ipmitool lan print 1 | grep 'IP Address'"
        cmd_proc = SimpleProcess(cmd)
        result = list(cmd_proc.run())

        for i in range(2):
            if not isinstance(result[i], str):
                result[i] = result[i].decode("utf-8")

        if result[1] or result[2]:
            msg = f"Failed to get BMC IP. Command: '{cmd}', Return Code: '{result[2]}'."
            for i in range(2):
                if result[i]:
                    res = result[i].replace('\r','').replace('\n','')
                    msg += f' {res}.'
            raise VError(errno.EINVAL, msg)

        bmc_ip = result[0].split()[-1]
        return bmc_ip

    def __get_bmc_power_status(self, node):
        """ Get BMC power status
        """

        cmd = f"ssh {node} ipmitool chassis status | grep 'System Power'"
        cmd_proc = SimpleProcess(cmd)
        result = list(cmd_proc.run())

        for i in range(2):
            if not isinstance(result[i], str):
                result[i] = result[i].decode("utf-8")

        if result[1] or result[2]:
            msg = f"Failed to get BMC power status. Command: '{cmd}', Return Code: '{result[2]}'."
            for i in range(2):
                if result[i]:
                    res = result[i].replace('\r','').replace('\n','')
                    msg += f' {res}.'
            raise VError(errno.EINVAL, msg)

        pw_status = result[0].split()[-1]
        return pw_status, cmd, result

    def __ping_bmc(self, node):
        """ Ping BMC IP
        """
        ip = self.__get_bmc_ip(node)

        cmd = f"ssh {node} ping -c 1 -W 1 {ip}"
        cmd_proc = SimpleProcess(cmd)
        result = list(cmd_proc.run())

        if result[1] or result[2]:
            msg = f"Ping failed for IP '{ip}'. Command: '{cmd}', Return Code: '{result[2]}'."
            for i in range(2):
                if result[i]:
                    if not isinstance(result[i], str):
                        result[i] = result[i].decode("utf-8")
                    res = result[i].replace('\r','').replace('\n','')
                    msg += f' {res}.'
            raise VError(errno.ECONNREFUSED, msg)

    def validate(self, v_type, args):
        """
        Process BMC validations.
        Usage (arguments to be provided):
        1. bmc accessible <node> <bmc_ip> <bmc_user> <bmc_passwd>
        2. bmc stonith <node> <bmc_ip> <bmc_user> <bmc_passwd>
        """
        if not isinstance(args, list):
            raise VError(errno.EINVAL, f"Invalid parameters '{args}'")

        if len(args) < 1:
            raise VError(errno.EINVAL, "No parameters specified")

        if len(args) < 4:
            raise VError(errno.EINVAL,
                    f"Insufficient parameters '{args}' for 'bmc validate'. Refer usage.")
        elif len(args) > 4:
            raise VError(errno.EINVAL,
                    f"Too many parameters '{args}' for 'bmc validate'. Refer usage.")

        if v_type == "accessible":
            self.validate_bmc_accessibility(args[0], args[1], args[2], args[3])
        elif v_type == "stonith":
            self.validate_bmc_stonith_config(args[0], args[1], args[2], args[3])
        else:
            raise VError(errno.EINVAL,f"Action parameter '{v_type}' not supported")

    def validate_bmc_accessibility(self, node, bmc_ip, bmc_user, bmc_passwd):
        """ Validate BMC accessibility
        """
        # Validate bmc accessibility on inband setup
        self.validate_inband_bmc_channel(node)
        # BMC IP based validations
        # Validate bmc accessibility on outband setup
        self.validate_bmc_channel_over_lan(bmc_ip, bmc_user, bmc_passwd)
        # Check if we can ping BMC
        self.__ping_bmc(node)

    def validate_bmc_stonith_config(self, node, bmc_ip, bmc_user, bmc_passwd):
        """ Validations for BMC STONITH Configuration
        """
        cmd = f"ssh {node} fence_ipmilan -P -a {bmc_ip} -o status -l {bmc_user} -p {bmc_passwd}"
        cmd_proc = SimpleProcess(cmd)
        result = list(cmd_proc.run())

        if result[1] or result[2]:
            msg = f"Failed to check BMC STONITH Config. Command: '{cmd}',\
                    Return Code: '{result[2]}'."
            for i in range(2):
                if result[i]:
                    if not isinstance(result[i], str):
                        result[i] = result[i].decode("utf-8")
                    res = result[i].replace('\r','').replace('\n','')
                    msg += f' {res}.'
            raise VError(errno.EINVAL, msg)

    def validate_inband_bmc_channel(self, node):
        """ Get BMC channel information (inband)
        """
        cmd = f"ssh {node} ipmitool {self.channel_cmd}"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        if rc != 0:
            msg = f"Failed to get BMC channel info of '{node}''. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)
        return True

    def validate_bmc_channel_over_lan(self, bmc_ip, bmc_user, bmc_passwd):
        """ Get BMC channel information over lan (out-of-band)
        """
        # check BMC ip is accessible over lan (out of band)
        cmd = f"ipmitool -H {bmc_ip} -U {bmc_user} -P {bmc_passwd} -I lan {self.channel_cmd}"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        if rc != 0:
            msg = f"Failed to get BMC channel info of '{bmc_ip}' over lan. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)
        return True
