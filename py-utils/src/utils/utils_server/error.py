#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

from collections import defaultdict

class RestServerError(Exception):
    """Error class for cortx rest server."""

    def __init__(self, e):
        self._e = e

    def http_error(self):
        return self._http_error(self._e)

    @staticmethod
    def _http_error(except_name):
        ret_code_map = defaultdict(lambda: 500)
        ret_code_map['KeyError'] = (418, "Wrong Key in payload!") # wrong key from client
        ret_code_map['KafkaException'] = (514, "MessageBus backend error!")
        return ret_code_map[except_name]

