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

    def validate(self, args):
        """Process consul valiations."""

        if not isinstance(args, list) or len(args) < 1:
            raise VError(errno.EINVAL, "Invalid parameters %s" % args)

        if args[0] == "service":
            if len(args) < 2:
                raise VError(errno.EINVAL, "Insufficient parameters.")

            ConsulV.validate_consul_service_status(args[1], args[2])

    @staticmethod
    def validate_consul_service_status(host, port):
        """Validate Consul service status."""

        url = f"http://{host}:{str(port)}/v1/status/leader"

        try:
            if requests.get(url).status_code != 200:
                raise VError(errno.ECONNREFUSED, "Consul is not running")
        except requests.exceptions.RequestException:
            raise VError(errno.ECONNREFUSED, "Consul is not running")
