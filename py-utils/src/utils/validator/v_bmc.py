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


class BmcV:
    """BMC related validations."""

    def __init__(self):
        self._network = NetworkV()


    def __get_bmc_ip(self):
        """ Get BMC IP along with status of command
        """

        cmd = "ipmitool lan print 1 | grep 'IP Address'"
        cmd_proc = SimpleProcess(cmd)
        result = cmd_proc.check_output(shell=True)

        if result[2]:
            raise VError(result[2], result[1])

        bmc_ip = result[0].split()[-1]
        return bmc_ip


    def __get_bmc_power_status(self):
        """ Get BMC power status
        """

        cmd = "ipmitool chassis status | grep 'System Power'"
        cmd_proc = SimpleProcess(cmd)
        result = cmd_proc.check_output(shell=True)

        if result[2]:
            raise VError(result[2], result[1])

        pw_status = result[0].split()[-1]
        return pw_status


    def ping_bmc(self):
        """ Ping BMC IP
        """
        ip = self.__get_bmc_ip()
        self._network.validate_ip_connectivity([ip])


    def validate(self, v_type, args):
        """
        Process BMC validations.
        Usage (arguments to be provided):
        1. bmc accessible
        2. bmc stonith
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) > 0:
            raise VError(errno.EINVAL, "'%s' parameters not required" % args)

        if v_type == "accessible":
            self.validate_bmc_accessibility()
        elif v_type == "stonith_cfg":
            self.validate_bmc_stonith_config()
        else:
            raise VError(
                errno.EINVAL, "Action parameter %s not supported" % v_type)


    def validate_bmc_accessibility(self):
        """ Validate Consul service status.
        """

        # Validate BMC power status
        pw_status = self.__get_bmc_power_status()
        if pw_status != 'on':
            raise VError(errno.EINVAL, f"BMC Power Status : {pw_status}")

        # Check if we can ping BMC
        self.ping_bmc()


    def validate_bmc_stonith_config(self):
        """ Validations for BMC STONITH Configuration
        """

        node_res = PillarGet.get_pillar("cluster:node_list")
        if node_res[2]:
            raise VError(errno.EINVAL, f"Failed to get nodes : {node_res}")

        nodes = node_res[0]
        for node in nodes:
            bmc_ip_get = PillarGet.get_pillar(f"cluster:{node}:bmc:ip")
            if bmc_ip_get[2]:
                raise VError(errno.EINVAL, f"Failed to get BMC IP : {bmc_ip_get}")

            user = PillarGet.get_pillar(f"cluster:{node}:bmc:user")
            if user[2]:
                raise VError(errno.EINVAL, f"Failed to get BMC user : {user}")

            secret = PillarGet.get_pillar(f"cluster:{node}:bmc:secret")
            if secret[2]:
                raise VError(errno.EINVAL, f"Failed to get BMC secret : {secret}")

            decrypt_passwd = decrypt_secret("cluster", secret[0])
            if decrypt_passwd[2]:
                raise VError(errno.EINVAL, f"Failed to decrypt BMC secret : {decrypt_passwd}")

            bmc_ip = bmc_ip_get[0]
            bmc_user = user[0]
            bmc_passwd = decrypt_passwd[0]

            cmd = f"fence_ipmilan -P -a {bmc_ip} -o status -l {bmc_user} -p {bmc_passwd}"
            cmd_proc = SimpleProcess(cmd)
            run_result = list(cmd_proc.run())

            if run_result[2]:
                raise VError(errno.EINVAL, f"ERROR: Please Check BMC STONITH Config : {run_result}")
