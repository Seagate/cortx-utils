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
import sys
import unittest

from cortx.utils.discovery import Discovery
from cortx.utils.discovery.resource_map import ResourceMap

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'conf_sample.json')

discovery = Discovery()
ResourceMap.index = "test_healthmap"
ResourceMap.url = "json://%s" % file_path
ResourceMap.load()

rpath1 = "nodes[0]>compute[0]>hw>disks"
rpath2 = "nodes[0]>storage[0]>hw"


class TestDiscovery(unittest.TestCase):
    """Test Discovery module interfaces"""

    def test_generate_node_health_ok(self):
        """Check for request acceptance and successful health generation"""
        status = discovery.generate_node_health(rpath1)
        self.assertEqual(status, "Success")
        status = discovery.generate_node_health(rpath2)
        self.assertEqual(status, "Success")

    def test_get_gen_node_health_status_ok(self):
        """Check for generator health status"""
        import pdb;pdb.set_trace()
        status = discovery.get_gen_node_health_status()
        self.assertEqual(status, "Success")
        discovery.generate_node_health(rpath1)
        status = discovery.get_gen_node_health_status()
        self.assertEqual(status, "Success")

    def test_get_node_health_ok(self):
        """Check for node health information collected"""
        discovery.generate_node_health(rpath1)
        info = discovery.get_node_health(rpath1)
        # TODO: Enable assertNotEqual to {} once
        # ResourceMap can serve health information
        self.assertEqual({}, info)
        #self.assertNotEqual({}, info)

    def test_get_resource_map_ok(self):
        """Check show resource map interface is not throwing any error"""
        discovery.get_resource_map(rpath1)
        discovery.get_resource_map(rpath2)


if __name__ == '__main__':
    unittest.main()
