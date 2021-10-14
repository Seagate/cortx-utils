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

target_path = '/tmp/testSB'
class TestSupportBundle(unittest.TestCase):
    """Test Support Bundle related functionality."""

    _cluster_conf_path = ''
    @classmethod
    def setUpClass(cls, cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """Test Setup class."""
        from cortx.utils.log import Log
        Log.init('support_bundle', '/var/log/cortx/utils/suppoort/', \
            level='DEBUG', backup_count=5, file_size_in_mb=5)
        cls.sb_description = "Test support bundle generation"
        if TestSupportBundle._cluster_conf_path:
            cls.cluster_conf_path = TestSupportBundle._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path

    def test_001_verify_SB_generate_single_comp(self):
        """Validate SB generate for single component."""
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                target_path=target_path, cluster_conf=TestSupportBundle.cluster_conf_path)
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
                target_path=target_path, cluster_conf=TestSupportBundle.cluster_conf_path)
        bundle_path = bundle_obj.bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_obj.bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name   ), True)

    def test_011_verify_SB_generate_after_rsyslog_service_stop(self):
        """Validate SB generate while rsyslog service is down."""
        cmd = "systemctl stop rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                target_path=target_path, cluster_conf=TestSupportBundle.cluster_conf_path)
        bundle_path = bundle_obj.bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_obj.bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name   ), True)
        cmd = "systemctl start rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        ServiceV().validate('isrunning', ['rsyslog'])

    def test_013_verify_SB_generate_after_elasticsearch_service_stop(self):
        """Validate SB generate while elasticsearch service is down."""
        cmd = "systemctl stop elasticsearch"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        bundle_obj = SupportBundle.generate(
            comment=TestSupportBundle.sb_description, \
                target_path=target_path, cluster_conf=TestSupportBundle.cluster_conf_path)
        bundle_path = bundle_obj.bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_obj.bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)
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
            comment=TestSupportBundle.sb_description, target_path=target_path, \
                cluster_conf=TestSupportBundle.cluster_conf_path)
        bundle_path = bundle_obj.bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_obj.bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)
        status = SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        self.assertIsNotNone(status)
        self.assertIsInstance(status, str)
        if 'Success' in status:
            import re
            status_bundle_id = re.search(r'/SB........', status).group(0)[1:]
            self.assertEqual(bundle_obj.bundle_id, status_bundle_id)
            cmd = "pcs cluster start --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)

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
    import sys
    if len(sys.argv) >= 2:
        TestSupportBundle._cluster_conf_path  = sys.argv.pop()
    unittest.main()
