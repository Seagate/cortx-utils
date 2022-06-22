#!/bin/python3

# CORTX Python common library.
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


class Service:
    """
    This Abstract class will serve as base for all service validators.

    The classes will extend this and provide their implementation of
    validate_service_status.
    """

    def __init__(self):
        pass

    def validate_service_status(self):
        pass


class HttpService(Service):
    """
    This class has validate_service_status implementation that makes http call.

    to check if service is up and running.
    """

    def __init__(self, service_name, host, port, service_url=""):
        super(HttpService, self).__init__()

        self.service_name = service_name
        self.host = host
        self.port = port
        self.service_url = service_url

    def validate_service_status(self):
        """Validate service status."""

        url = f"http://{self.host}:{self.port}{self.service_url}"

        try:
            status_code = requests.get(url).status_code
            if status_code != 200:
                raise VError(
                    errno.ECOMM, (f"Error {status_code} obtained while "
                    f"connecting to {self.service_name} service on {self.host}:{self.port}."))
        except requests.exceptions.InvalidURL:
            raise VError(
                errno.EINVAL, (f"Either or all inputs host '{self.host}' and port "
                f"'{self.port}' are invalid."))
        except requests.exceptions.ConnectionError:
            raise VError(errno.ECONNREFUSED,
                         f"No {self.service_name} service running on {self.host}:{self.port}")
        except requests.exceptions.RequestException as req_ex:
            raise VError(
                errno.ECOMM, (f"Error connecting to {self.service_name} service on "
                f"{self.host}:{self.port}. {req_ex}"))

