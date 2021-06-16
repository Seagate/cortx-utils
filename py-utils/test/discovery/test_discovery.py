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
from cortx.utils.discovery.error import DiscoveryError

# Sample rpaths
#valid_rpath = "nodes[0]"
#valid_rpath = "nodes[0]>compute[0]"
#valid_rpath = "nodes[0]>storage[0]"
valid_rpath = "nodes[0]>storage[0]>hw>controllers"
invalid_rpath = "nodes[0]>notexist[0]"


class TestDiscovery(unittest.TestCase):
    """Test Discovery module interfaces"""

    def test_generate_node_health(self):
        """Check for immediate request id """
        request_id = Discovery.generate_node_health(valid_rpath)
        self.assertIsNotNone(request_id)

    def test_get_gen_node_health_status_success(self):
        """Check for node health status using valid request_id"""
        request_id = Discovery.generate_node_health(valid_rpath)
        status = Discovery.get_gen_node_health_status(request_id)
        self.assertEqual(status, "Success")

    def test_get_node_health(self):
        """Check for generated recource map location"""
        req_id = Discovery.generate_node_health(valid_rpath)
        url = Discovery.get_node_health(req_id)
        self.assertIsNotNone(url)

    def test_generate_node_health_on_invalid_rpath(self):
        """Check for failed status on invalid rpath"""
        req_id = Discovery.generate_node_health(invalid_rpath)
        status = Discovery.get_gen_node_health_status(req_id)
        self.assertIn("Failed", status)
        self.assertIn("Invalid rpath", status)

    def test_get_gen_node_health_status_with_invalid_id(self):
        """Check for node health status with invalid request id"""
        request_id = "xxxxxxxxxxx"
        self.assertRaises(
            DiscoveryError, Discovery.get_gen_node_health_status, request_id)

    def test_get_node_health_with_invalid_id(self):
        """Check for node health backend url with invalid id"""
        request_id = "xxxxxxxxxxx"
        self.assertRaises(
            DiscoveryError, Discovery.get_node_health, request_id)


if __name__ == '__main__':
    unittest.main()
