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
from psutil import process_iter
from cortx.utils.validator.error import VError
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_network import NetworkV

class ServiceV:
	"""Service related validations."""

	def validate(self, v_type: str, args: list, host: str = None,
				 is_process : bool = False, username : str = None,
				 is_command : bool = False):
		"""
		Process service validations.
		Usage (arguments to be provided):
		1. service isrunning host (optional) [servicenames]
		2. service isrunning [processnames] username (optional) is_process=True
		3. service isrunning [commands] username (optional) is_command=True
		"""

		# Ensure we can perform passwordless ssh and there are no prompts
		if host:
			NetworkV().validate('passwordless',
				[pwd.getpwuid(os.getuid()).pw_name, host])

		if v_type == "isrunning":
			if is_process:
				return self.validate_processes(args, username)
			elif is_command:
				return self.validate_cmdline(args, username)
			else:
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
			# To calm down codacy.
			stdout = stdout

	def validate_processes(self, process_list : list, username : str):
		""" Validates if processes are running :
			Validate if bare processes (eg.consul) are running
			which can not be validated using systemctl status.
		"""
		process_list = [proc.lower() for proc in process_list]
		running_pl = []

		for proc_obj in process_iter():
			if proc_obj.name().lower() in process_list:
				if not username or username == proc_obj.username():
					running_pl.append(proc_obj.name().lower())

		error_str = "Process '%s' is not running" + \
					(f" with user {username}" if username else '')

		for proc in process_list:
			if proc not in running_pl:
				raise VError(errno.EINVAL,
							 error_str % proc)

	def validate_cmdline(self, cmd_list : list, username : str):
		""" Validates if terminal commands are running :
			eg. validate if "vim /var/log/cortx/sspl/sspl.log" is running.
				validate if "sh /some/location/mock_server.sh" is running.
		"""
		cmd_list = [" ".join(cmd.split()) for cmd in cmd_list]
		running_cmd = []

		for proc_obj in process_iter():
			if " ".join(proc_obj.cmdline()) in cmd_list:
				if not username or username == proc_obj.username():
					running_cmd.append(" ".join(proc_obj.cmdline()))

		error_str = "Command '%s' is not running" + \
					(f" with user {username}" if username else '')

		for cmd in cmd_list:
			if cmd not in running_cmd:
				raise VError(errno.EINVAL,
							 error_str % cmd)
