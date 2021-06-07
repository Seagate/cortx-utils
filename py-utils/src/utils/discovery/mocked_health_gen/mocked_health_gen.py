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

script_path = os.path.realpath(__file__)
data_file = os.path.join(os.path.dirname(script_path), "mocked_node_health.json")
mock_index = "mock_index"
Conf.load(mock_index, "json://%s" % data_file)


class Server:
    """Provides health information of FRUs in storage"""

    name = "server"

    def get_health_info(self, rpath):
        """
        Fetch health information for given FRU
        rpath: Resouce id (Example: nodes[0]>compute[0]>hw>disks)
        """
        return Conf.get(mock_index, rpath)


class Storage:
    """Provides health information of FRUs in storage"""

    name = "storage"

    def get_health_info(self, rpath):
        """
        Fetch health information for given FRU
        rpath: Resouce id (Example: nodes[0]>storage[0]>hw>controllers)
        """
        return Conf.get(mock_index, rpath)


if __name__ == "__main__":
    storage = Storage()
    storage.get_health_info(rpath="nodes[0]>storage[0]>hw>controllers")
