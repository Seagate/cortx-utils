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
from psutil import process_iter
from cortx.utils.validator.error import VError

class ProcessV:
    """Process related validations."""
    
    def validate(self, v_type: str, args: list,
                 username: str = None, is_cmd: bool = False):
        """
		Process validations.
		Usage (arguments to be provided):
		1. isrunning [processnames] username (optional)
	    2. isrunning [commands] username (optional) is_command=True
		"""

        if v_type == "isrunning":
            if is_cmd:
                return self.validate_cmdline(args, username)
            else:
                return self.validate_processes(args, username)
        else:
            raise VError(errno.EINVAL,
				     "Action parameter %s not supported" % v_type)

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
