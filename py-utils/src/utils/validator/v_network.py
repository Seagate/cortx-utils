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


class NetworkV:
    """Network related validations."""

    def validate(self, v_type, args):
        """
        Process network validations.
        Usage (arguments to be provided):
        1. network connectivity <ip1> <ip2> <ip3>
        2. network passwordless <user> <node1> <node2>
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if len(args) < 1:
            raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

        if v_type == "connectivity":
            self.validate_ip_connectivity(args)
        elif v_type == "passwordless":
            self.validate_passwordless_ssh(args[0], args[1:])
        else:
            raise VError(
                errno.EINVAL, "Action parameter %s not supported" % v_type)

    def validate_ip_connectivity(self, ips):
        """Check if IP/Hosts are reachable."""

        unreachable_ips = []
        for ip in ips:
            cmd = f"ping -c 1 -W 1 {ip}"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[2]:
                unreachable_ips.append(ip)

        if len(unreachable_ips) != 0:
            raise VError(
                errno.ECONNREFUSED, "Ping failed for IP/Host(s). %s" % unreachable_ips)

    def validate_passwordless_ssh(self, user, nodes):
        """Check passwordless ssh."""

        for node in nodes:
            cmd = ("ssh -o PreferredAuthentications=publickey "
                   f"-o StrictHostKeyChecking=no {user}@{node} /bin/true")
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                raise VError(errno.ECONNREFUSED,
                             f"Passwordless ssh not configured for {node}.")

    def _is_valid_ipv4_part(self, ip_part):
        try:
            return str(int(ip_part)) == ip_part and 0 <= int(ip_part) <= 255
        except Exception:
            return False
