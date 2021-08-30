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
import json
import time
import unittest
from cortx.utils.support_framework import SupportBundle
from cortx.utils.support_framework import Bundle


class TestSupportBundle(unittest.TestCase):

    """Test Support Bundle related functionality."""
    from cortx.utils.log import Log
    Log.init('support_bundle', '/var/log/cortx/utils/suppoort/', level='DEBUG', \
        backup_count=5, file_size_in_mb=5)
    sb_description = "Test support bundle generation"

    def test_001generate(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['provisioner'])
        self.assertIsNotNone(bundle_obj)
        self.assertIsInstance(bundle_obj, Bundle)
        self.assertIsInstance(bundle_obj.bundle_id, str)
        self.assertIsInstance(bundle_obj.bundle_path, str)
        self.assertNotEqual(bundle_obj.bundle_id, '')
        self.assertNotEqual(bundle_obj.bundle_path, '')
        self.assertEqual(bundle_obj.comment, self.sb_description)
        self.assertEqual(os.path.exists(f'{bundle_obj.bundle_path}'), True)

    def test_002generated_path(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['csm'])
        time.sleep(10)
        from cortx.utils.conf_store import Conf
        Conf.load('cluster_conf', 'json:///etc/cortx/cluster.conf')
        node_name = Conf.get('cluster_conf', 'cluster>srvnode-1')
        tar_file_name = f"{bundle_obj.bundle_id}_{node_name}.tar.gz"
        sb_file_path = f'{bundle_obj.bundle_path}/{bundle_obj.bundle_id}/{node_name}/{tar_file_name}'
        self.assertEqual(os.path.exists(sb_file_path), True)

    def test_003status(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['csm'])
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsInstance(status, str)
        self.assertIsInstance(json.loads(status), dict)

    def test_004status(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['csm'])
        time.sleep(5)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], "Success")

    def test_005status(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['wrong'])
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        status = json.loads(status)
        self.assertEqual(status['status'], [])

    def test_006status(self):
        # TODO - Once all components are working this test case can be removed
        # Getting error because of some components dont have support.yaml and
        # empty support.yaml
        bundle_obj = SupportBundle.generate(comment=self.sb_description)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')
    
    def test_007_wrong_comp(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['util'])
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')
    
    def test_008_wrong_comp(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['util;csmm'])
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')
    
    def test_009_wrong_comp(self):
        bundle_obj = SupportBundle.generate(comment=self.sb_description, components=['util;csm'])
        time.sleep(10)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')

if __name__ == '__main__':
    unittest.main()
