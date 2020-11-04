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

from cortx.utils.validator.service import HttpService
from cortx.utils.validator.error import VError


class ElasticsearchV(HttpService):
    """Elasticsearch related validations."""

    def __init__(self):
        super(ElasticsearchV, self).__init__()

        self.service_name = "elasticsearch"
        self.service_url = ""

    def validate(self, v_type, args):
        """
        Process elasticsearch validations.
        Usage (arguments to be provided):
        1. elasticsearch service localhost 9200
        """

        if not isinstance(args, list):
            raise VError(errno.EINVAL, f"Invalid parameters {args}")

        if len(args) < 2:
            raise VError(errno.EINVAL, f"Insufficient parameters. {args}")

        if v_type == "service":
            self.host = args[0]
            self.port = args[1]
            self.validate_service_status()
        else:
            raise VError(
                errno.EINVAL, f"Action parameter {v_type} not supported")

