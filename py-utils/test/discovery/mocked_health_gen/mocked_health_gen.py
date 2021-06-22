#!/bin/python3

# CORTX Python common library.
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
# please email opensource@seagate.com or cortx-questions@seagate.com

import os

from cortx.utils.conf_store import Conf
from cortx.utils.discovery.node_health import common_config

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

dir_path = os.path.dirname(os.path.realpath(__file__))
store_path = os.path.join(dir_path, 'mocked_node_health.json')
store_type = "json"
mock_data_url = "%s://%s" % (store_type, store_path)
mock_index = "mock_index"
Conf.load(mock_index, mock_data_url)


class Server:
    """Provides health information of FRUs in storage"""

    name = "server"

    def get_health_info(self, rpath):
        """
        Fetch health information for given FRU
        rpath: Resouce id (Example: node>compute[0]>hw>disks)
        """
        return Conf.get(mock_index, rpath)


class Storage:
    """Provides health information of FRUs in storage"""

    name = "storage"

    def get_health_info(self, rpath):
        """
        Fetch health information for given FRU
        rpath: Resouce id (Example: node>storage[0]>hw>controllers)
        """
        return Conf.get(mock_index, rpath)


if __name__ == "__main__":
    storage = Storage()
    storage.get_health_info(rpath="node>storage[0]>hw>controllers")
