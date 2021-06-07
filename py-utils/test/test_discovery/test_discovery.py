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

import unittest

from cortx.utils.discovery import Discovery
from cortx.utils.discovery.node_health import NodeHealth
from cortx.utils.discovery.resource import Resource

data_file = "/tmp/test_resource_health_map.json"
NodeHealth.url = "json://%s" % data_file
Resource.init(NodeHealth.url)

rpath1 = "nodes[0]>storage[0]"
rpath2 = "nodes[0]>compute[0]>hw>disks[0]>health>status"

discovery = Discovery()


class TestDiscovery(unittest.TestCase):
    """Test Discovery module interfaces"""

    def test_get_gen_node_health_status(self):
        """Check for generate node health readiness"""
        status = discovery.get_gen_node_health_status()
        self.assertTrue(
            any(res for res in ["Ready", "Success", "Failed"] if res in status),
            "Unexpected generate node health status - '%s'" % status)

    def test_get_gen_node_health_status_success(self):
        """
        Check for generate node health status is successful
        on processing the request.
        """
        discovery.generate_node_health(rpath1)
        status = discovery.get_gen_node_health_status()
        self.assertEqual(status, "Success")

    def test_get_gen_node_health_status_inprogress(self):
        """
        Check for generate node health status is in-progress
        with previous request.
        """
        # Set generate node health task is inprogress
        NodeHealth.STATUS = "In-progress"
        try:
            status = discovery.get_gen_node_health_status()
        except:
            pass
        # Reset
        NodeHealth.STATUS = "Ready"
        self.assertEqual(
            status, "In-progress",
            "Generate node health is not processing.")

    def test_generate_node_health_success(self):
        """Check for request acceptance and successful health generation"""
        status = discovery.generate_node_health(rpath1)
        self.assertEqual(status, "Success", "Failed")

    def test_generate_node_health_failed(self):
        """Check for request denied or failed status"""
        NodeHealth.STATUS = "In-progress"
        status = ""
        try:
            status = discovery.generate_node_health(rpath1)
        except:
            pass
        NodeHealth.STATUS = "Ready"
        self.assertIn("Failed", status, "New request is not denied.")

    def test_get_node_health(self):
        """Check for fetching node health backend URL"""
        url = discovery.get_node_health()
        self.assertEqual(url, NodeHealth.URL,
            "Node health backend url is invalid.")


if __name__ == '__main__':
    unittest.main()
