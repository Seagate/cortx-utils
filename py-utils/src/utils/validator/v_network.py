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
import socket
from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess


class NetworkV:
    """Network related validations."""

    def validate(self, v_type, args):
        """
        Process network validations.
        Usage (arguments to be provided):
        1. network connectivity <ip1> <ip2> <host>
        2. network passwordless <user> <node1> <node2>
        3. network drivers <driver_name> <node1> <node2>
        4. network hca <provider> <node1> <node2>
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if v_type == "connectivity":
            if len(args) < 1:
                raise VError(errno.EINVAL,
                             "Insufficient parameters. %s" % args)
            self.validate_host_connectivity(args)

        else:
            if len(args) < 2:
                raise VError(errno.EINVAL,
                             "Insufficient parameters. %s" % args)

            if v_type == "passwordless":
                self.validate_passwordless_ssh(args[0], args[1:])
            elif v_type == "drivers":
                self.validate_network_drivers(args[0], args[1:])
            elif v_type == "hca":
                # More providers can be added to the list in future, if required.
                self.hca_checks = ['mellanox']
                if args[0].lower() not in self.hca_checks:
                    raise VError(errno.EINVAL,
                                 "Invalid HCA Provider name. "
                                 "Please choose from  %s" % self.hca_checks)
                self.validate_hca(args[0], args[1:])
            else:
                raise VError(errno.EINVAL,
                             "Action parameter %s not supported" % v_type)

    def validate_ip_connectivity(self, ips):
        """Check if IPs are reachable."""

        unreachable_ips = []
        for ip in ips:
            if ip.count(".") == 3 and all(self._is_valid_ipv4_part(ip_part)
                                          for ip_part in ip.split(".")):

                cmd = f"ping -c 1 -W 1 {ip}"
                cmd_proc = SimpleProcess(cmd)
                run_result = cmd_proc.run()

                if run_result[2]:
                    unreachable_ips.append(ip)
            else:
                raise VError(errno.EINVAL, f"Invalid ip {ip}.")

        if len(unreachable_ips) != 0:
            raise VError(
                errno.ECONNREFUSED, "Ping failed for IP(s). %s" % unreachable_ips)

    def validate_host_connectivity(self, hosts):
        """Check if hosts are reachable."""
        for host in hosts:
            ip = host
            if not self._is_ip(ip):
                ip = self._resolve_host(host)
            self.validate_ip_connectivity([ip])

    def validate_passwordless_ssh(self, user, nodes):
        """Check passwordless ssh."""

        for node in nodes:
            cmd = ("ssh -o PreferredAuthentications=publickey "
                   f"-o StrictHostKeyChecking=no {user}@{node} /bin/true")
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = (f"Passwordless ssh not configured for {node}."
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.ECONNREFUSED, res)

    def _is_ip(self, ip):
        return (ip.count(".") == 3 and all(self._is_valid_ipv4_part(ip_part)
                for ip_part in ip.split(".")))

    def _is_valid_ipv4_part(self, ip_part):
        try:
            return str(int(ip_part)) == ip_part and 0 <= int(ip_part) <= 255
        except Exception:
            return False

    def _resolve_host(self, host):
        try:
            return socket.gethostbyname(host)
        except Exception as exc:
            raise VError(errno.EINVAL,
                         f"Failed to resolve host {host} Error {str(exc)}")

    def validate_network_drivers(self, driver, nodes):
        """Check if drivers (eg: Mellanox OFED) are proper"""

        for node in nodes:
            cmd = f"ssh {node} rpm -qa | grep {driver}"
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()

            if run_result[1] or run_result[2]:
                res = (f"Given Driver '{driver}' Is Not Installed on {node}. "
                       f"Also, check if '{node}' is valid. "
                       f"CMD {cmd} failed. {run_result[0]}. {run_result[1]}")
                raise VError(errno.EINVAL, res)

    def validate_hca(self, provider, nodes):
        """Check if HCA presence and ports"""

        for node in nodes:
            if provider.lower() in self.hca_checks:
                cmd = f"ssh {node} lspci -nn | grep '{provider.capitalize()}'"
                cmd_proc = SimpleProcess(cmd)
                run_result = cmd_proc.run()

                if run_result[1] or run_result[2]:
                    res = (f"{provider.capitalize()} Host Channel Adapters card "
                           f"(possibly with Infiniband capability) is not detected on {node}. "
                           f"Also, check if '{node}' is valid. "
                           f"CMD '{cmd} failed. {run_result[0]}. {run_result[1]}")
                    raise VError(errno.EINVAL, res)

                ports_cmd = f"{cmd} | wc -l"
                ports_cmd_proc = SimpleProcess(ports_cmd)
                ports_run_result = ports_cmd_proc.run()

                if ports_run_result[1] or ports_run_result[2]:
                    res = (f"{provider.capitalize()} Host Channel Adapters ports were not "
                           f"detected by command {cmd}. "
                           f"Also, check if '{node}' is valid. "
                           f"CMD {cmd} failed. {ports_run_result[0]}. {ports_run_result[1]}")
                    raise VError(errno.EINVAL, res)

                res = (ports_run_result[0].decode('utf-8').strip())
                if int(res) == 0:
                    res = (f"{provider.capitalize()} Host Channel Adapters ports were not "
                           f"detected by command {cmd}. "
                           "For high-speed data network, it is expected to "
                           "have at least one port present over some PCIe slot. ")
                    raise VError(errno.EINVAL, res)
