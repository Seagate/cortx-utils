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
import sys

from cortx.utils import const
from cortx.utils.conf_store import Conf
from cortx.utils.discovery import Discovery
from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.kv_store import KvStoreFactory

# Load cortx common config
store_type = "json"
config_url = "%s://%s" % (store_type, const.CORTX_CONF_FILE)
common_config = KvStoreFactory.get_instance(config_url)
common_config.load()

# Load mock data
test_dir = os.path.dirname(os.path.realpath(__file__))
health_store_path = os.path.join(test_dir, 'solution/lr2/health.json')
manifest_store_path = os.path.join(test_dir, 'solution/lr2/manifest.json')
mock_health_data_url = "%s://%s" % (store_type, health_store_path)
mock_manifest_data_url = "%s://%s" % (store_type, manifest_store_path)
mock_health = "mock-health"
mock_manifest = "mock-manifest"
Conf.load(mock_health, mock_health_data_url)
Conf.load(mock_manifest, mock_manifest_data_url)

# Sample rpaths
#valid_rpath = "node"
#valid_rpath = "node>compute[0]"
#valid_rpath = "node>storage[0]"
valid_rpath = "node>storage[0]>hw>controller"
invalid_rpath = "node>notexist[0]"


class TestDiscovery(unittest.TestCase):
    """Test Discovery module interfaces"""

    def setUp(self):
        self.solution_platform_monitor = common_config.get(
            ["discovery>solution_platform_monitor"])[0]
        # Set platform monitor path to mocked data path
        common_config.set(
            ["discovery>solution_platform_monitor"],
            ["cortx/utils/test/discovery/solution"])

    def test_generate_node_health(self):
        """Check for immediate request id"""
        request_id = Discovery.generate_node_health(valid_rpath)
        self.assertIsNotNone(request_id)

    def test_get_gen_node_health_status_success_on_health(self):
        """Check for node health status using valid request_id"""
        request_id = Discovery.generate_node_health(valid_rpath)
        status = Discovery.get_gen_node_health_status(request_id)
        self.assertEqual(status, "Success")

    def test_get_node_health(self):
        """Check for generated resource map location"""
        req_id = Discovery.generate_node_health(valid_rpath)
        url = Discovery.get_node_health(req_id)
        self.assertIsNotNone(url)

    def test_get_node_health_static_store_url(self):
        """Check for static store url"""
        request_id = Discovery.generate_node_health()
        url = Discovery.get_node_health(request_id)
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

    def test_generate_node_manifest(self):
        """Check for immediate request id"""
        request_id = Discovery.generate_node_manifest(valid_rpath)
        self.assertIsNotNone(request_id)

    def test_get_gen_node_manifest_success_on_manifest(self):
        """Check for manifest request status using valid request_id"""
        request_id = Discovery.generate_node_manifest(valid_rpath)
        status = Discovery.get_gen_node_manifest_status(request_id)
        self.assertEqual(status, "Success")

    def test_get_node_manifest(self):
        """Check for generated manifest location"""
        req_id = Discovery.generate_node_manifest(valid_rpath)
        url = Discovery.get_node_manifest(req_id)
        self.assertIsNotNone(url)

    def tearDown(self):
        # Reset platform monitor path
        common_config.set(
            ["discovery>solution_platform_monitor"],
            [self.solution_platform_monitor])


if __name__ == '__main__':
    unittest.main()
