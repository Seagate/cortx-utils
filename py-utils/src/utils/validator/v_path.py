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

class PathV:
	"""Pkg related validations."""

	def __run_cmd(self, cmd):
		# print(f"Running {cmd}")
		handler = SimpleProcess(cmd)
		stdout, stderr, retcode = handler.run()
		if retcode != 0:
			raise VError(errno.EINVAL,
				     "cmd: %s failed with error code: %d stderr: %s"
				     %(cmd, retcode, stderr))
		if stderr:
			raise VError(errno.EINVAL,
				     "cmd: %s failed with stderr: %s"
				     %(cmd, stderr))
		# To calm down codacy.
		return stdout.decode("utf-8")

	def validate(self, v_type: str, args: list, host: str = None):
		"""
		Process path validations.

                Usage (arguments to be provided):
		1. path exists host (optional) [<type>:<absolute_path>]
                   Note: Supported type keywords: file, dir, link, device.
                """
		# Ensure we can perform passwordless ssh and there are no prompts
		if host:
			NetworkV().validate('passwordless',
				[pwd.getpwuid(os.getuid()).pw_name, host])

		if v_type == "exists":
			return self.validate_paths(host, args)
		else:
			raise VError(errno.EINVAL,
				     "Action parameter %s not supported" % v_type)

	def validate_paths(self, host, paths):
		"""Check if path are found and matching."""
		for path in paths:
			if ":" not in path:
				raise VError(errno.EINVAL,
					     "Input should contain colon ':' separated values, given: %s" % path)
			_type = path.split(":")[0]
			_path = path.split(":")[1]
			if _type not in ["file", "dir", "link", "device"]:
				raise VError(errno.EINVAL,
					     "invalid type: %s" % _type)
			if _type == "file":
				__type = "regular file"
			elif _type == "dir":
				__type = "directory"
			elif _type == "link":
				__type = "symbolic link"
			elif _type == "device":
				__type = "block special file"
			else:
				raise VError(errno.EINVAL,
					     "Invalid type: %s" % _type)

			if _path == "":
				raise VError(errno.EINVAL,
					     "Absolute path must be provided, given: %s!" % path)
			if host != None:
				result = self.__run_cmd(f"ssh {host} stat {_path} --printf=%F")
			else:
				result = self.__run_cmd(f"stat {_path} --printf=%F")
			if result.find(f"{__type}") == -1:
				raise VError(errno.EINVAL,
					     "object: %s not found" % path)


