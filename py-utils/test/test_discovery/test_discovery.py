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
from cortx.utils.discovery.resource import Resource

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'conf_sample.json')

Resource.index = "test_healthmap"
Resource.url = "json://%s" % file_path
Resource.init(Resource.url)

rpath1 = "nodes[0]>compute[0]>hw>psus"
rpath2 = "nodes[0]>compute[0]>hw>disks[0]>health>status"
rpath3 = "nodes[0]>storage[0]>fw"

discovery = Discovery()


class TestDiscovery(unittest.TestCase):
    """Test Discovery module interfaces"""

    def test_get_gen_node_health_status_ok(self):
        """Check for generator health status"""
        status = discovery.get_gen_node_health_status()
        self.assertIn(status, ["Ready", "Success"])
        discovery.generate_node_health(rpath1)
        status = discovery.get_gen_node_health_status()
        self.assertEqual(status, "Success")

    def test_generate_node_health_ok(self):
        """Check for request acceptance and successful health generation"""
        status = discovery.generate_node_health(rpath1)
        self.assertEqual(status, "Success")

    def test_get_node_health_ok(self):
        """Check for node health information is 'OK'"""
        health = discovery.get_node_health(rpath2)
        self.assertNotIn(health, [{}, None, "", []])
        self.assertEqual(health, "OK")

    def test_get_resource_map_ok(self):
        """Check list of resource maps collected"""
        rmap = discovery.get_resource_map(rpath3)
        self.assertNotIn(rmap, [{}, None, "", []])

if __name__ == '__main__':
    unittest.main()
