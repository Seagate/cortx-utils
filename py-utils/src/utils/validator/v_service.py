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

import os
import pwd
import errno
from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_network import NetworkV

class ServiceV:
	"""Service related validations."""

	def validate(self, v_type: str, args: list, host: str = None):
		"""
		Process service validations.
		Usage (arguments to be provided):
		1. service isrunning host (optional) [servicenames]
		"""

		# Ensure we can perform passwordless ssh and there are no prompts
		if host:
			NetworkV().validate('passwordless',
				[pwd.getpwuid(os.getuid()).pw_name, host])

		if v_type == "isrunning":
			return self.validate_services(host, args)
		else:
			raise VError(errno.EINVAL,
				     "Action parameter %s not supported" % v_type)

	def validate_services(self, host, services):
		"""Check if services are running."""

		for service in services:
			if host != None:
				cmd = f"ssh {host} systemctl status {service}"
			else:
				cmd = f"systemctl status {service}"
			handler = SimpleProcess(cmd)
			_, stderr, retcode = handler.run()
			if retcode != 0:
				raise VError(errno.EINVAL,
					     "cmd: %s failed with error code: %d"
					     %(cmd, retcode))
			if stderr:
				raise VError(errno.EINVAL,
					     "cmd: %s failed with stderr: %s"
					     %(cmd, stderr))
