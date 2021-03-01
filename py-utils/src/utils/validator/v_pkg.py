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

	def __search_pkg(self, cmd):
		# print(f"Running {cmd}")
		handler = SimpleProcess(cmd)
		stdout, stderr, retcode = handler.run()
		if retcode != 0:
			raise VError(errno.EINVAL,
				     "cmd: %s failed with error code: %d, stderr: %s"
				     %(cmd, retcode, stderr))
		return stdout.decode("utf-8")

	def validate(self, v_type: str, args: list, host: str = None):
		"""
		Process rpm validations.
		Usage (arguments to be provided):
		1. pkg validate_rpms host (optional) [packagenames]
		2. pkg validate_pip3s host (optional) [pip3 packagenames]
		"""

		# Ensure we can perform passwordless ssh and there are no prompts
		if host:
			NetworkV().validate('passwordless',
				[pwd.getpwuid(os.getuid()).pw_name, host])

		if v_type == "rpms":
			return self.validate_rpms(host, args)
		elif v_type == "pip3s":
			return self.validate_pip3s(host, args)
		else:
			raise VError(errno.EINVAL,
				     "Action parameter %s not supported" % v_type)

	def validate_rpms(self, host, pkgs):
		"""Check if rpm pkg is installed."""

		if host != None:
			result = self.__search_pkg(f"ssh {host} rpm -qa")
		else:
			result = self.__search_pkg("rpm -qa")

		for pkg in pkgs:
			if result.find(f"{pkg}") == -1:
				raise VError(errno.EINVAL,
					     "rpm pkg: %s not found" % pkg)

	def validate_pip3s(self, host, pkgs, skip_version_check=True):
		"""Check if pip3 pkg is installed."""

		if not isinstance(pkgs, dict):
			skip_version_check = True

		if host != None:
			result = self.__search_pkg(f"ssh {host} pip3 list")
		else:
			result = self.__search_pkg("pip3 list")

		for pkg in pkgs:
			if result.find(f"{pkg}") == -1:
				raise VError(errno.EINVAL,
							"pip3 pkg: %s not found" % pkg)
			if not skip_version_check:
				matched_str = re.search(f"{pkg} \((.*)\)", result)
				installed_version = matched_str.groups()[0]
				expected_version = pkgs[pkg]
				if installed_version != expected_version:
					err_desc = "pip3 pkg: %s is not having expected version. " + \
     							"Installed: %s Expected: %s"
					raise VError(errno.EINVAL,
								err_desc % (pkg, installed_version, expected_version))
