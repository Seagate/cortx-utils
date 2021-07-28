#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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
# please email opensource@seagate.com or cortx-questions@seagate.com.


import os
import unittest
from cortx.utils.support_framework import SupportBundle
from cortx.utils.support_framework import Bundle



class TestSupportBundle(unittest.TestCase):
    """ Test Support Bundle related functionality. """

    sb_description = "Test support bundle generation"
    bundle_obj = SupportBundle.generate(comment=sb_description, components=['provisioner'])

    def test_001generate(self):
        self.assertIsNotNone(self.bundle_obj)
        self.assertIsInstance(self.bundle_obj, Bundle)
        self.assertIsInstance(self.bundle_obj.bundle_id, str)
        self.assertIsInstance(self.bundle_obj.bundle_path, str)
        self.assertNotEqual(self.bundle_obj.bundle_id, '')
        self.assertNotEqual(self.bundle_obj.bundle_path, '')
        self.assertEqual(self.bundle_obj.comment, self.sb_description)
    
    def test_002generated_path(self):
        from cortx.utils.conf_store import Conf
        Conf.load('index', 'json:///etc/cortx/cluster.conf')
        node_name = Conf.get('index', 'server_node>hostname')
        tar_file_name = f"{self.bundle_obj.bundle_id}_{node_name}.tar.gz"
        sb_file_path = f'/var/log/seagate/support_bundle/{tar_file_name}'
        self.assertTrue(os.path.exists(sb_file_path))

    def test_003status(self):
        status = SupportBundle.get_status(bundle_id=self.bundle_obj.bundle_id)
        self.assertNotEqual(status, {})
        self.assertIsInstance(status, dict)
       

if __name__ == '__main__':
    unittest.main()
