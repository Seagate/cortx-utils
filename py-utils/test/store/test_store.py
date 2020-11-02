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

from cortx.utils.store.pillar import PillarDB
from cortx.utils.store.kvstore import KvManager
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestStore(unittest.TestCase):
    """Test store related functionality."""

    def test_pillerdb_get_management_vip(self):
        """Test Get Management VIP from PillarDB."""

        kv = KvManager(PillarDB())
        mgmt_vip = kv.get('cluster:mgmt_vip')

        self.assertIsNotNone(mgmt_vip, "Management VIPs not found")
        self.assertTrue(
            TestStore._is_valid_ipv4(mgmt_vip),
            "Invalid Management VIP")

    def test_pillerdb_get_cluster_ip(self):
        """Test Get Cluster IP from PillarDB."""

        kv = KvManager(PillarDB())
        cluster_ip = kv.get('cluster:cluster_ip')

        self.assertIsNotNone(cluster_ip, "Cluster IP not found")
        self.assertTrue(
            TestStore._is_valid_ipv4(cluster_ip),
            "Invalid Cluster IP")

    def test_pillerdb_get_nodes(self):
        """Test Get Node list from PillarDB."""

        kv = KvManager(PillarDB())
        ips = kv.get('cluster:node_list')

        assert_msg = "Nodes not found"
        self.assertIsNotNone(ips, assert_msg)
        self.assertGreater(len(ips), 0, assert_msg)

    @staticmethod
    def _is_valid_ipv4(ip):
        isValid = False
        if ip.count(".") == 3 and all(TestStore._is_valid_ipv4_part(ip_part)
                                      for ip_part in ip.split(".")):
            isValid = True

        return isValid

    @staticmethod
    def _is_valid_ipv4_part(ip_part):
        try:
            return str(int(ip_part)) == ip_part and 0 <= int(ip_part) <= 255
        except Exception:
            return False


if __name__ == '__main__':
    unittest.main()
