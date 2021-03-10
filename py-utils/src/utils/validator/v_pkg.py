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
from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_network import NetworkV

class PkgV:
    """Pkg related validations."""

    def __execute_cmd(self, cmd):
        """Execute command and return decoded string as result."""
        handler = SimpleProcess(cmd)
        stdout, stderr, retcode = handler.run()
        result = stdout.decode("utf-8") if retcode ==0 else stderr.decode("utf-8")
        if retcode != 0:
            raise VError(
                errno.EINVAL,
                "Command failure. cmd: %s stderr: %s" %(cmd, result))
        return result

    def validate(self, v_type: str, args: list, host: str = None):
        """
        Process rpm validations.
        Usage (arguments to be provided):
        1. pkg validate_rpms host (optional) [packagenames]
        2. pkg validate_pip3s host (optional) [pip3 packagenames]
        """
        if host:
            # Ensure we can perform passwordless ssh and there are no prompts
            NetworkV().validate('passwordless',
                [pwd.getpwuid(os.getuid()).pw_name, host])

        if v_type == "rpms":
            return self.validate_rpm_pkgs(host, args)
        elif v_type == "pip3s":
            return self.validate_pip3_pkgs(host, args)
        else:
            raise VError(errno.EINVAL, "Action parameter %s not supported" % v_type)

    def validate_rpm_pkgs(self, host, pkgs, skip_version_check=True):
        """Check if rpm pkg is installed."""
        if not isinstance(pkgs, dict):
            skip_version_check = True

        rpm_cmd = "ssh %s rpm -qa" % host if host else "rpm -qa"
        result = self.__execute_cmd(rpm_cmd)

        for pkg in pkgs:
            if result.find("%s" % pkg) == -1:
                raise VError(errno.EINVAL, "rpm pkg %s not installed." % pkg)
            if not skip_version_check:
                matched_str = re.search(r"%s-([^-][0-9.]+)-" % pkg, result)
                installed_version = matched_str.groups()[0]
                expected_version = pkgs[pkg]
                if installed_version != expected_version:
                    raise VError(errno.EINVAL, "Mismatched version for rpm package %s. " \
                        "Installed %s. Expected %s." %(pkg, installed_version, expected_version))

    def validate_pip3_pkgs(self, host, pkgs, skip_version_check=True):
        """Check if pip3 pkg is installed."""
        if not isinstance(pkgs, dict):
            skip_version_check = True

        pip3_cmd = "ssh %s pip3 list" % host if host else "pip3 list"
        result = self.__execute_cmd(pip3_cmd)

        for pkg in pkgs:
            if result.find("%s" % pkg) == -1:
                raise VError(errno.EINVAL, "pip3 pkg %s not installed." % pkg)
            if not skip_version_check:
                matched_str = re.search(r"%s \((.*)\)" % pkg, result)
                installed_version = matched_str.groups()[0]
                expected_version = pkgs[pkg]
                if installed_version != expected_version:
                    raise VError(errno.EINVAL, "Mismatched version for pip3 package %s. " \
                        "Installed %s. Expected %s." %(pkg, installed_version, expected_version))
