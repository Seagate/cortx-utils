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

import re
import os
import pwd
import errno
import socket
from cortx.utils.ssh import SSHChannel
from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_network import NetworkV


class PkgV:
    """Pkg related validations."""

    def __init__(self):
        self.passwdless_ssh_enabled = False
        self.ssh = None

    def __execute_cmd(self, cmd):
        """
        Execute command using SSHChannel or SimpleProcees and returns result.

        Uses SimpleProcess to execute the command on passwordless ssh configured
        host. Otherwise, uses SSHChannel to execute command.
        """
        if self.ssh:
            retcode, result = self.ssh.execute(cmd)
        else:
            handler = SimpleProcess(cmd)
            stdout, stderr, retcode = handler.run()
            result = stdout.decode("utf-8") if retcode == 0 else stderr.decode("utf-8")
        if retcode != 0:
            raise VError(errno.EINVAL,
                "Command failure. cmd: %s stderr: %s" % (cmd, result))
        return result

    def validate(self, v_type: str, args: list, host: str = None):
        """
        Process rpm validations.

        Usage (arguments to be provided):
        1. pkg validate_rpms host (optional) [packagenames]
        2. pkg validate_pip3s host (optional) [pip3 packagenames]
        host should be host url in case passwordless ssh is not configured.
        host url format - user:passwd@fqdn:port
        """
        host = socket.getfqdn() if host == None or host == "localhost" else host
        host_details = re.search(r"(\w+):(.+)@(.+):(\d+)", host)
        if host_details:
            user = host_details.groups()[0]
            passwd = host_details.groups()[1]
            host = host_details.groups()[2]
            port = host_details.groups()[3]
            self.ssh = SSHChannel(host=host, username=user, password=passwd, port=port)
        elif host != socket.getfqdn():
            # Ensure we can perform passwordless ssh and there are no prompts
            NetworkV().validate("passwordless",
                [pwd.getpwuid(os.getuid()).pw_name, host])
            self.passwdless_ssh_enabled = True

        if v_type == "rpms":
            return self.validate_rpm_pkgs(host, args)
        elif v_type == "pip3s":
            return self.validate_pip3_pkgs(host, args)
        else:
            raise VError(errno.EINVAL, "Action parameter %s not supported" % v_type)

        if self.ssh:
            self.ssh.disconnect()

    def validate_rpm_pkgs(self, host, pkgs, skip_version_check=True):
        """Check if rpm pkg is installed."""
        cmd = "ssh %s rpm -qa" % host if self.passwdless_ssh_enabled else "rpm -qa"
        result = self.__execute_cmd(cmd)

        if not isinstance(pkgs, dict):
            skip_version_check = True

        for pkg in pkgs:
            if result.find("%s" % pkg) == -1:
                raise VError(errno.EINVAL,
                    "rpm pkg %s not installed on host %s." % (pkg, host))
            if not skip_version_check:
                matched_str = re.search(r"%s-([^-][0-9.]+)-" % pkg, result)
                installed_version = matched_str.groups()[0]
                expected_version = pkgs[pkg]
                if installed_version != expected_version:
                    raise VError(errno.EINVAL,
                        "Mismatched version for rpm package %s on host %s. Installed %s. Expected %s."
                        % (pkg, host, installed_version, expected_version))

    def validate_pip3_pkgs(self, host, pkgs, skip_version_check=True):
        """Check if pip3 pkg is installed."""
        cmd = "ssh %s pip3 list" % host if self.passwdless_ssh_enabled else "pip3 list"
        result = self.__execute_cmd(cmd)

        if not isinstance(pkgs, dict):
            skip_version_check = True

        for pkg in pkgs:
            if result.find("%s" % pkg) == -1:
                raise VError(errno.EINVAL,
                    "pip3 pkg %s not installed on host %s." % (pkg, host))
            if not skip_version_check:
                matched_str = re.search(r"%s \((.*)\)" % pkg, result)
                installed_version = matched_str.groups()[0]
                expected_version = pkgs[pkg]
                if installed_version != expected_version:
                    raise VError(errno.EINVAL,
                        "Mismatched version for pip3 package %s on host %s. Installed %s. Expected %s."
                        % (pkg, host, installed_version, expected_version))
