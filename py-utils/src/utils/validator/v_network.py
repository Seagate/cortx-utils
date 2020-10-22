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


class NetworkV:
    """Network related validations."""

    @classmethod
    def validate(self, args):
        """Process network validations."""

        if not isinstance(args, list) or len(args) < 1:
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        action = args[0]

        if action == "management_vip":
            self.validate_management_vip(args[1])
        elif action == "cluster_ip":
            self.validate_cluster_ip(args[1])
        elif action == "public_data_ips":
            self.validate_public_data_ips(args[1:])
        elif action == "private_data_ips":
            self.validate_private_data_ips(args[1:])
        elif action == "controllers":
            self.validate_controllers(args[1:])

        raise VError(errno.EINVAL, "Invalid parameter %s" % args)

    @classmethod
    def validate_management_vip(self, management_vip):
        """Validate Management VIP."""

        unreachable_ips = self.validate_ip_connectivity([management_vip])
        if len(unreachable_ips) != 0:
            raise VError(errno.ECONNREFUSED,
                         f"Pinging Management VIP {management_vip} failed")

        return

    @classmethod
    def validate_cluster_ip(self, cluster_ip):
        """ Validate Cluster IP."""

        unreachable_ips = self.validate_ip_connectivity([cluster_ip])
        if len(unreachable_ips) != 0:
            raise VError(errno.ECONNREFUSED,
                         f"Pinging Cluster IP {cluster_ip} failed")

        return

    @classmethod
    def validate_public_data_ips(self, public_data_ips):
        """Validate Public data IPs."""

        unreachable_ips = self.validate_ip_connectivity(public_data_ips)
        if len(unreachable_ips) != 0:
            raise VError(
                errno.ECONNREFUSED, f"Pinging following Public data Ips {ITEMS_SEPARATOR.join(unreachable_ips)} failed")

        return

    @classmethod
    def validate_private_data_ips(self, private_data_ips):
        """Validate Private data IPs."""

        unreachable_ips = self.validate_ip_connectivity(private_data_ips)
        if len(unreachable_ips) != 0:
            raise VError(
                errno.ECONNREFUSED, f"Pinging following Private data Ips {ITEMS_SEPARATOR.join(unreachable_ips)} failed")

        return

    @classmethod
    def validate_controllers(self, controller_ips):
        """Validate Controllers."""

        unreachable_ips = self.validate_ip_connectivity(controller_ips)
        if len(unreachable_ips) != 0:
            raise VError(
                errno.ECONNREFUSED, f"Pinging following Controllers {ITEMS_SEPARATOR.join(unreachable_ips)} failed")

        return

    @classmethod
    def validate_ip_connectivity(self, ips):
        """Check if IPs are reachable."""

        unreachable_ips = []
        for ip in ips:
            cmd = f"ping -c 1 {ip}"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[2]:
                unreachable_ips.append(ip)

        return unreachable_ips
