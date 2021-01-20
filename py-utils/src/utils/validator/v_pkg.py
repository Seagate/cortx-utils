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

class PkgV:
	"""Pkg related validations."""

	def __search_pkg(self, cmd):
		# print(f"Running {cmd}")
		handler = SimpleProcess(cmd)
		stdout, stderr, retcode = handler.run()
		if retcode != 0:
			raise VError(errno.EINVAL,
				     "cmd: %s failed with error code: %d"
				     %(cmd, retcode))
		if stderr:
			raise VError(errno.EINVAL,
				     "cmd: %s failed with stderr: %s"
				     %(cmd, stderr))

	def validate(self, v_type: str, args: list, host: str = None):
		"""
		Process rpm validations.
		Usage (arguments to be provided):
		1. pkg validate_rpms host (optional) [packagenames]
		2. pkg validate_pip3s host (optional) [pip3 packagenames]
		"""

		if v_type == "rpms":
			return self.validate_rpms(host, args)
		elif v_type == "pip3s":
			return self.validate_pip3s(host, args)
		else:
			raise VError(errno.EINVAL,
				     "Action parameter %s not supported" % v_type)

	def validate_rpms(self, host, pkgs):
		"""Check if rpm pkg is installed."""

		for pkg in pkgs:
			if host != None:
				self.__search_pkg(f"ssh {host} rpm -qa | grep {pkg}")
			else:
				self.__search_pkg(f"rpm -qa | grep {pkg}")

	def validate_pip3s(self, host, pkgs):
		"""Check if pip3 pkg is installed."""

		for pkg in pkgs:
			if host != None:
				self.__search_pkg(f"ssh {host} pip3 list --format=legacy | grep {pkg}")
			else:
				self.__search_pkg(f"pip3 list --format=legacy {pkg}")
