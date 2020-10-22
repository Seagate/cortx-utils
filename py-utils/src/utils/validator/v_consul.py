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
import requests

from cortx.utils.validator.error import VError


class ConsulV:
    """Consul related validations."""

    @classmethod
    def validate(self, args):
        """
        Process consul validations.
        Usage (arguments to be provided):
        1. consul service localhost 8500
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        args_length = len(args)

        if args_length == 0:
            raise VError(errno.EINVAL, "Action parameter not provided")

        if args[0] == "service":
            if args_length < 3:
                raise VError(
                    errno.EINVAL, f"Insufficient parameters for action '{args[0]}' provided. Expected 2 but provided {args_length - 1}")

            self.validate_service_status(args[1], args[2])
        else:
            raise VError(errno.EINVAL, "Action parameter %s not supported" % args[0])

    @classmethod
    def validate_service_status(self, host, port):
        """Validate Consul service status."""

        url = f"http://{host}:{str(port)}/v1/status/leader"

        try:
            if requests.get(url).status_code != 200:
                raise VError(errno.ECONNREFUSED, "Consul is not running")
        except requests.exceptions.RequestException:
            raise VError(errno.ECONNREFUSED, "Consul is not running")
