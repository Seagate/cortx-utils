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
from cortx.utils.ssh import SSHSession


class BmcV:
    """BMC related validations."""

    def __init__(self):
        self.channel_cmd = "channel info"
        self.session = None

    def __get_bmc_ip(self, node):
        """ Get BMC IP along with status of command
        """
        cmd = "ipmitool lan print 1 | grep 'IP Address'"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        rc = stdout.channel.recv_exit_status()
        if rc != 0 :
            msg = f"Failed to get BMC IP of {node}. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.read().decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)
        bmc_ip = cmd_output.split()[-1]
        return bmc_ip

    def __get_bmc_power_status(self, node):
        """ Get BMC power status
        """
        cmd = "ipmitool chassis status | grep 'System Power'"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        rc = stdout.channel.recv_exit_status()
        if rc != 0 :
            msg = f"Failed to get BMC power status of {node}. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.read().decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)
        pw_status = cmd_output.split()[-1]
        return pw_status

    def __ping_bmc(self, node):
        """ Ping BMC IP
        """
        ip = self.__get_bmc_ip(node)
        cmd = f"ping -c 1 -W 1 {ip}"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        rc = stdout.channel.recv_exit_status()
        if rc != 0 :
            msg = f"Ping failed for IP '{ip}'. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.read().decode("utf-8").replace('\r','').replace('\n','')
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

        # Root user to execute ipmitool command
        user = "root"
        node = args[0]
        self.session = SSHSession(node, user, use_pkey=True)

        if v_type == "accessible":
            self.validate_bmc_accessibility(node, args[1], args[2], args[3])
        elif v_type == "stonith":
            self.validate_bmc_stonith_config(node, args[1], args[2], args[3])
        else:
            raise VError(errno.EINVAL,f"Action parameter '{v_type}' not supported")

        self.session.disconnect()

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
        cmd = f"fence_ipmilan -P -a {bmc_ip} -o status -l {bmc_user} -p {bmc_passwd}"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            msg = f"Failed to check BMC STONITH Config. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.read().decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)

    def validate_inband_bmc_channel(self, node):
        """ Get BMC channel information (inband)
        """
        cmd = f"ipmitool {self.channel_cmd}"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            msg = f"Failed to get BMC channel info of '{node}''. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.read().decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)
        return True

    def validate_bmc_channel_over_lan(self, bmc_ip, bmc_user, bmc_passwd):
        """ Get BMC channel information over lan (out-of-band)
        """
        # check BMC ip is accessible over lan (out of band)
        cmd = f"ipmitool -H {bmc_ip} -U {bmc_user} -P {bmc_passwd} -I lan {self.channel_cmd}"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            msg = f"Failed to get BMC channel info of '{bmc_ip}' over lan. Command: '{cmd}',\
                    Return Code: '{rc}'."
            msg += stderr.read().decode("utf-8").replace('\r','').replace('\n','')
            raise VError(errno.EINVAL, msg)
        return True
