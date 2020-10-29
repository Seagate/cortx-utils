#!/usr/bin/env python3

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

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from cortx.utils.store.pillar import PillarDB
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.store.error import KvError


class TestPillar(unittest.TestCase):
    """Test pillar related functionality."""

    def test_management_vip(self):
        """Validate Management VIP."""
        ips = PillarDB().get('cluster:mgmt_vip')
        print(ips)
        NetworkV().validate('connectivity', ips)

    def test_cluster_ip(self):
        """Validate Management VIP."""
        ips = PillarDB().get('cluster:cluster_ip')
        print(ips)
        NetworkV().validate('connectivity', ips)

    def test_nodes(self):
        """Validate Management VIP."""
        ips = PillarDB().get('cluster:node_list')
        print(ips)
        NetworkV().validate('connectivity', ips)


if __name__ == '__main__':
    unittest.main()
