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
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.pillar_get import PillarGet
from cortx.utils.decrypt_secret import decrypt_secret
from cortx.utils.common import get_cmd_error_msg


class BmcV:
    """BMC related validations."""

    def __init__(self):
        self._network = NetworkV()


    def __get_bmc_ip(self, node):
        """ Get BMC IP along with status of command
        """

        cmd = f"ssh {node} ipmitool lan print 1 | grep 'IP Address'"
        cmd_proc = SimpleProcess(cmd)
        result = cmd_proc.run()

        if result[2]:
            msg = get_cmd_error_msg("Failed to get BMC IP.", cmd, result)
            raise VError(errno.EINVAL, msg)


        if not isinstance(result[0], str):
            result[0] = result[0].decode("utf-8")

        bmc_ip = result[0].split()[-1]
        return bmc_ip


    def __get_bmc_power_status(self, node):
        """ Get BMC power status
        """

        cmd = f"ssh {node} ipmitool chassis status | grep 'System Power'"
        cmd_proc = SimpleProcess(cmd)
        result = list(cmd_proc.run())

        if result[2]:
            msg = get_cmd_error_msg("Failed to get BMC power status.", cmd, result)
            raise VError(errno.EINVAL, msg)

        if not isinstance(result[0], str):
            result[0] = result[0].decode("utf-8")

        pw_status = result[0].split()[-1]
        return pw_status, cmd, result


    def ping_bmc(self, node):
        """ Ping BMC IP
        """
        ip = self.__get_bmc_ip(node)

        cmd = f"ssh {node} ping -c 1 -W 1 {ip}"
        cmd_proc = SimpleProcess(cmd)
        result = list(cmd_proc.run())

        if result[2]:
            msg = f"Ping failed for IP '{ip}'."
            raise VError(errno.ECONNREFUSED, get_cmd_error_msg(msg, cmd, result))


    def validate(self, v_type, args):
        """
        Process BMC validations.
        Usage (arguments to be provided):
        1. bmc accessible
        2. bmc stonith
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) < 1:
            raise VError(errno.EINVAL, "Insufficient parameters")

        if v_type == "accessible":
            self.validate_bmc_accessibility(args)
        elif v_type == "stonith":
            self.validate_bmc_stonith_config(args)
        else:
            raise VError(
                errno.EINVAL, "Action parameter '%s' not supported" % v_type)


    def validate_bmc_accessibility(self, nodes):
        """ Validate Consul service status.
        """
        for node in nodes:
            # Validate BMC power status
            pw_status, cmd, result = self.__get_bmc_power_status(node)
            if pw_status != 'on':
                msg = f"BMC Power Status : {pw_status}"
                raise VError(errno.EINVAL, get_cmd_error_msg(msg, cmd, result))

            # Check if we can ping BMC
            self.ping_bmc(node)


    def validate_bmc_stonith_config(self, nodes):
        """ Validations for BMC STONITH Configuration
        """

        for node in nodes:
            cmd, bmc_ip_get = PillarGet.get_pillar(f"cluster:{node}:bmc:ip")
            if bmc_ip_get[2]:
                msg = get_cmd_error_msg("Failed to get BMC IP", cmd, bmc_ip_get)
                raise VError(errno.EINVAL, msg)

            cmd, user = PillarGet.get_pillar(f"cluster:{node}:bmc:user")
            if user[2]:
                msg = get_cmd_error_msg("Failed to get BMC user", cmd, user)
                raise VError(errno.EINVAL, msg)

            cmd, secret = PillarGet.get_pillar(f"cluster:{node}:bmc:secret")
            if secret[2]:
                msg = get_cmd_error_msg("Failed to get BMC secret", cmd, secret)
                raise VError(errno.EINVAL, msg)

            cmd, decrypt_passwd = decrypt_secret("cluster", secret[0])
            if decrypt_passwd[2]:
                msg = get_cmd_error_msg("Failed to decrypt BMC secret", cmd, decrypt_passwd)
                raise VError(errno.EINVAL, msg)

            bmc_ip = bmc_ip_get[0]
            bmc_user = user[0]
            bmc_passwd = decrypt_passwd[0]

            cmd = f"fence_ipmilan -P -a {bmc_ip} -o status -l {bmc_user} -p {bmc_passwd}"
            cmd_proc = SimpleProcess(cmd)
            cmd, run_result = list(cmd_proc.run())

            if run_result[2]:
                msg = get_cmd_error_msg("Failed to check BMC STONITH Config", cmd, run_result)
                raise VError(errno.EINVAL, msg)
