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
from cortx.utils.conf_store import Conf
from cortx.utils.support_framework import Bundle
from cortx.utils.support_framework import SupportBundle
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_service import ServiceV


class TestSupportBundle(unittest.TestCase):

    """Test Support Bundle related functionality."""

    @classmethod
    def setUpClass(cls):
        """Test Setup class."""
        from cortx.utils.log import Log
        Log.init('support_bundle', '/var/log/cortx/utils/suppoort/', \
            level='DEBUG', backup_count=5, file_size_in_mb=5)
        cls.sb_description = "Test support bundle generation"
        Conf.load('cluster_conf', 'json:///etc/cortx/cluster.conf')
        cls.node_name = Conf.get('cluster_conf', 'cluster>srvnode-1')

    def test_001_verify_SB_generate_single_comp(self):
        """Validate SB generate for single component."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['provisioner'])
        self.assertIsNotNone(bundle_obj)
        self.assertIsInstance(bundle_obj, Bundle)
        self.assertIsInstance(bundle_obj.bundle_id, str)
        self.assertIsInstance(bundle_obj.bundle_path, str)
        self.assertNotEqual(bundle_obj.bundle_id, '')
        self.assertNotEqual(bundle_obj.bundle_path, '')
        self.assertEqual(bundle_obj.comment, TestSupportBundle.sb_description)
        self.assertEqual(os.path.exists(f'{bundle_obj.bundle_path}'), True)

    def test_002_verify_SB_generated_path(self):
        """Validate SB generated path."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['provisioner'])
        time.sleep(15)
        tar_file_name = f"{bundle_obj.bundle_id}_"\
            f"{TestSupportBundle.node_name}.tar.gz"
        sb_file_path = f"{bundle_obj.bundle_path}/{bundle_obj.bundle_id}/"\
            f"{TestSupportBundle.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)

    def test_003_verify_SB_get_status_success_single_comp(self):
        """Validate SB get_status success for single component."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, components=['utils'])
        time.sleep(15)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        self.assertIsInstance(status, str)
        self.assertIsInstance(json.loads(status), dict)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Success')

    def test_004_verify_SB_get_status_success_multi_comp(self):
        """Validate SB get_status success for multiple components."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['csm', 'utils'])
        time.sleep(30)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        self.assertIsInstance(status, str)
        self.assertIsInstance(json.loads(status), dict)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Success')
            self.assertEqual(status['status'][0]['result'], 'Success')

    def test_005_verify_SB_get_status_empty_invalid_comp(self):
        """Validate SB get_status empty for invalid component."""
        # TODO - This test can be removed once bug(EOS-24882) is fixed
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, components=['wrong'])
        time.sleep(10)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        status = json.loads(status)
        self.assertEqual(status['status'], [])

    def test_006_verify_SB_get_status_all_comp(self):
        """Validate SB get_status for all component."""
        # TODO - Once all components are working this test case can be removed
        # Getting error because of some components dont have support.yaml and
        # empty support.yaml
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description)
        time.sleep(20)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')

    def test_007_verify_SB_get_status_error_invalid_comp(self):
        """Validate SB get_status error for invalid component."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, components=['util'])
        time.sleep(10)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')

    def test_008_verify_SB_get_status_error_multi_invalid_comp(self):
        """Validate SB get_status error for multiple invalid components."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['util', 'csmm'])
        time.sleep(15)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')

    def test_009_verify_SB_generate_comp_dir_remove(self):
        """Validate component directories are removed after SB generate."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, components=['csm'])
        time.sleep(10)
        self.assertFalse(os.path.exists(f'{bundle_obj.bundle_path}/\
            {bundle_obj.bundle_id}/{TestSupportBundle.node_name}/csm'))

    def test_010_verify_SB_generate_multi_comp_dir_remove(self):
        """Validate multipe component directories are removed after SB generate."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['csm', 'provisioner'])
        time.sleep(15)
        self.assertFalse(os.path.exists(f'{bundle_obj.bundle_path}/\
            {bundle_obj.bundle_id}/{TestSupportBundle.node_name}/csm'))
        self.assertFalse(os.path.exists(f'{bundle_obj.bundle_path}/\
            {bundle_obj.bundle_id}/{TestSupportBundle.node_name}/provisioner'))

    def test_011_verify_SB_generate_after_rsyslog_service_stop(self):
        """Validate SB generate while rsyslog service is down."""
        cmd = "systemctl stop rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['provisioner'])
        time.sleep(15)
        tar_file_name = f"{bundle_obj.bundle_id}_"\
            f"{TestSupportBundle.node_name}.tar.gz"
        sb_file_path = f"{bundle_obj.bundle_path}/{bundle_obj.bundle_id}/"\
            f"{TestSupportBundle.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)
        cmd = "systemctl start rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        ServiceV().validate('isrunning', ['rsyslog'])

    def test_012_verify_SB_get_status_error_single_invalid_comp(self):
        """Validate SB get_status error for single invalid component."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, components=['util;csm'])
        time.sleep(15)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')

    def test_013_verify_SB_generate_after_elasticsearch_service_stop(self):
        """Validate SB generate while elasticsearch service is down."""
        cmd = "systemctl stop elasticsearch"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                components=['provisioner'])
        time.sleep(15)
        tar_file_name = f"{bundle_obj.bundle_id}_"\
            f"{TestSupportBundle.node_name}.tar.gz"
        sb_file_path = f"{bundle_obj.bundle_path}/{bundle_obj.bundle_id}/"\
            f"{TestSupportBundle.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)
        cmd = "systemctl start elasticsearch"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        ServiceV().validate('isrunning', ['elasticsearch'])

    def test_014_verify_SB_get_status_after_cluster_stop(self):
        """Validate SB get_status while cluster is down."""
        cmd = "pcs cluster stop --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, components=['csm'])
        time.sleep(15)
        tar_file_name = f"{bundle_obj.bundle_id}_"\
            f"{TestSupportBundle.node_name}.tar.gz"
        sb_file_path = f"{bundle_obj.bundle_path}/{bundle_obj.bundle_id}/"\
            f"{TestSupportBundle.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        self.assertIsInstance(status, str)
        print(status)
        status = json.loads(status)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Success')
            cmd = "pcs cluster start --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        time.sleep(5)

    @classmethod
    def tearDownClass(cls):
        """Test teardown class."""
        cmds = ["systemctl start rsyslog", "systemctl start elasticsearch", \
            "pcs cluster start --all"]
        for cmd in cmds:
            cmd_proc = SimpleProcess(cmd)
            _, _, rc = cmd_proc.run()
            assert(rc == 0)


if __name__ == '__main__':
    unittest.main()
