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
import yaml
import time
import unittest
from cortx.utils.conf_store import Conf
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_service import ServiceV


dir_path = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(dir_path, 'config.yaml')
with open(config_file) as test_args:
    configs = yaml.safe_load(test_args)

def SB_generate_CLI(target_path: str, cluster_conf_path: str):
    """Executes SB generate CLI command for the given component."""
    cmd = f"support_bundle generate 'sample comment' -t '{target_path}' -cp '{cluster_conf_path}'"
    cmd_proc = SimpleProcess(cmd)
    return cmd_proc.run()

def SB_get_status_CLI(bundle_id: str, cluster_conf_path: str):
    """Executes SB get_status CLI command for the given bundle_id."""
    cmd = f"support_bundle get_status -b '{bundle_id}' -cp '{cluster_conf_path}'"
    cmd_proc = SimpleProcess(cmd)
    return cmd_proc.run()


class TestSupportBundleCli(unittest.TestCase):
    """Test case will test available API's of Support Bundle."""

    cluster_conf_path = ''
    @classmethod
    def setUpClass(cls, cluster_conf_path = None):
        """Test Setup class."""
        if cluster_conf_path is not None:
            cls.cluster_conf_path = cluster_conf_path
        elif TestSupportBundleCli.cluster_conf_path:
            cls.cluster_conf_path = TestSupportBundleCli.cluster_conf_path
        else:
            cls.cluster_conf_path = 'yaml:///etc/cortx/cluster.conf'

    def test_001_cli_verify_SB_generate(self):
        """Validate SB generate for single component."""
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)

    def test_003_cli_verify_SB_get_status_success(self):
        """Validate SB get_status success for single component."""
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = ''
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        stdout, stderr, rc = SB_get_status_CLI(bundle_id, self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertIsInstance(status, str)
        import re
        status_bundle_id = re.search(r'/SB........', status).group(0)[1:]
        self.assertEqual(bundle_id, status_bundle_id)

    def test_006_cli_verify_SB_generate_help_response(self):
        """Validate SB generate help command response."""
        cmd = "support_bundle generate -h"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertEqual(status, configs['SB_generate_help'])

    def test_007_cli_verify_SB_get_status_help_response(self):
        """Validate SB get_status help command response."""
        cmd = "support_bundle get_status -h"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertEqual(status, configs['SB_get_status_help'])

    def test_008_cli_verify_SB_generated_path(self):
        """Validate SB generated path."""
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        bundle_path = stdout.decode('utf-8').split('->')[1].strip()[:-1]
        bundle_path = bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)

    def test_009_cli_verify_SB_generate_after_rsyslog_service_stop(self):
        """Validate SB generate while rsyslog service is down."""
        cmd = "systemctl stop rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        bundle_path = stdout.decode('utf-8').split('->')[1].strip()[:-1]
        bundle_path = bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)
        cmd = "systemctl start rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        ServiceV().validate('isrunning', ['rsyslog'])

    def test_010_cli_verify_SB_generate_after_elasticsearch_service_stop(self):
        """Validate SB generate while elasticsearch service is down."""
        cmd = "systemctl stop elasticsearch"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        bundle_path = stdout.decode('utf-8').split('->')[1].strip()[:-1]
        bundle_path = bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)
        cmd = "systemctl start elasticsearch"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        ServiceV().validate('isrunning', ['elasticsearch'])

    def test_011_cli_verify_SB_generate_after_cluster_stop(self):
        """Validate SB generate while cluster is down."""
        cmd = "pcs cluster stop --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        bundle_path = stdout.decode('utf-8').split('->')[1].strip()[:-1]
        bundle_path = bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)
        cmd = "pcs cluster start --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)

    def test_012_cli_verify_SB_get_status_after_cluster_stop(self):
        """Validate SB get_status while cluster is down."""
        cmd = "pcs cluster stop --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        stdout, stderr, rc = SB_get_status_CLI(bundle_id.strip(), self.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertIsInstance(status, str)
        import re
        status_bundle_id = re.search(r'/SB........', status).group(0)[1:]
        self.assertEqual(bundle_id, status_bundle_id)
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
    if len(sys.argv) > 2:
        TestSupportBundleCli.cluster_conf_path = sys.argv.pop()
    unittest.main()
