#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import os
import unittest

from cortx.utils.discovery import Discovery
from cortx.utils.discovery.node_health import NodeHealth
from cortx.utils.discovery.resource import Resource

data_file = "/tmp/test_resource_health_map.json"
NodeHealth.url = "json://%s" % data_file
Resource.init(NodeHealth.url)

rpath1 = "nodes[0]>compute[0]>hw>disks"
rpath2 = "nodes[0]>compute[0]>hw>disks[0]>health>status"

discovery = Discovery()


class TestDiscovery(unittest.TestCase):
    """Test Discovery module interfaces"""

    def test_get_gen_node_health_status(self):
        """Check for generator health status"""
        status = discovery.get_gen_node_health_status()
        self.assertIn(
            status, ["Ready", "Success"], "DM inprogress unexpectedly.")
        discovery.generate_node_health(rpath1)
        status = discovery.get_gen_node_health_status()
        self.assertEqual(status, "Success")

    def test_generate_node_health(self):
        """Check for request acceptance and successful health generation"""
        status = discovery.generate_node_health(rpath1)
        self.assertEqual(
            status, "Success", "Failed to generate node health")

    def test_get_node_health(self):
        """Check for node health information is 'OK'"""
        health = discovery.get_node_health(rpath2)
        self.assertTrue(
            True if health else False,
            "Health information not fouhd for given rpath.")

    def test_get_resource_map(self):
        """Check list of resource maps collected"""
        rmap = discovery.get_resource_map(rpath1)
        self.assertTrue(
            True if rmap else False,
            "Resource map not found for given rpath.")


if __name__ == '__main__':
    unittest.main()
