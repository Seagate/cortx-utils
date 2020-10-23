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

        if len(args) < 3:
            raise VError(errno.EINVAL, "Insufficient parameters. %s" % args)

        if args[0] == "service":
            self.validate_service_status(args[1], args[2])
        else:
            raise VError(
                errno.EINVAL, "Action parameter %s not supported" % args[0])

    @classmethod
    def validate_service_status(self, host, port):
        """Validate Consul service status."""

        url = f"http://{host}:{port}/v1/status/leader"

        try:
            response_status_code = requests.get(url).status_code
            if response_status_code != 200:
                raise VError(errno.ECOMM,
                             f"Error connecting to consul service on {host}:{port} with status code {response_status_code}.")
        except requests.exceptions.InvalidURL:
            raise VError(
                errno.EINVAL, f"Either or all inputs host '{host}' and port '{port}' are invalid.")
        except requests.exceptions.ConnectionError:
            raise VError(errno.ECONNREFUSED,
                         f"No Consul service running on {host}:{port}")
        except requests.exceptions.RequestException as req_ex:
            raise VError(errno.ECOMM,
                         f"Error connecting to consul service on {host}:{port}. {req_ex}")
