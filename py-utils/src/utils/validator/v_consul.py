#!/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import subprocess

from cortx.utils.validator.error import VError
from cortx.utils import const


class ConsulV:
    """ Consul related validations """

    def validate(self, args):
        """ Process consul valiations """

        if not isinstance(args, list) or len(args) < 1:
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if args[0] == "service":
            self.validate_service()

        raise VError(errno.EINVAL, "Invalid parameter %s" % args)

    def validate_service(self):
        """ Check Consul service """

        check_output_log = subprocess.check_output(
            const.CONSUL_STATUS_CHECK_CMD, shell=True)

        for log_line in check_output_log.splitlines():
            if const.CONSUL_STATUS_RUNNING in log_line.decode("utf-8"):
                return

        raise VError(errno.ENOENT, "Consul is not running")
