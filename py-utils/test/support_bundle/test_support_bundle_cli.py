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
import string
import random
import unittest
from cortx.utils.conf_store import Conf
from cortx.utils.process import SimpleProcess


dir_path = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(dir_path, 'config.yaml')
with open(config_file) as test_args:
    configs = yaml.safe_load(test_args)

def generate_bundle_id():
    """Generate Unique Bundle ID."""
    alphabet = string.ascii_lowercase + string.digits
    return f"SB{''.join(random.choices(alphabet, k=5))}"

def SB_generate_CLI(target_path: str, cluster_conf_path: str):
    """Executes SB generate CLI command for the given component."""
    cmd = f"cortx_support_bundle generate -m 'test' -b '{generate_bundle_id()}' -t '{target_path}' -c '{cluster_conf_path}'"
    cmd_proc = SimpleProcess(cmd)
    return cmd_proc.run()

def SB_get_status_CLI(bundle_id: str, cluster_conf_path: str):
    """Executes SB get_status CLI command for the given bundle_id."""
    cmd = f"cortx_support_bundle get_status -b '{bundle_id}' -c '{cluster_conf_path}'"
    cmd_proc = SimpleProcess(cmd)
    return cmd_proc.run()


class TestSupportBundleCli(unittest.TestCase):
    """Test case will test available API's of Support Bundle."""

    _cluster_conf_path = ''
    @classmethod
    def setUpClass(cls, cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """Test Setup class."""
        if TestSupportBundleCli._cluster_conf_path:
            cls.cluster_conf_path = TestSupportBundleCli._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path

    def test_001_cli_verify_cortx_SB_generate(self):
        """Validate SB generate."""
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], TestSupportBundleCli.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)

    def test_002_cli_verify_cortx_SB_get_status_success(self):
        """Validate SB get_status success."""
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], TestSupportBundleCli.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        stdout, stderr, rc = SB_get_status_CLI(bundle_id, TestSupportBundleCli.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertIsInstance(status, str)
        self.assertIn("Successfully generated SB", status)

    def test_003_cli_verify_cortx_SB_generate_help_response(self):
        """Validate SB generate help command response."""
        cmd = "cortx_support_bundle generate -h"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertEqual(status, configs['SB_generate_help'])

    def test_004_cli_verify_cortx_SB_get_status_help_response(self):
        """Validate SB get_status help command response."""
        cmd = "cortx_support_bundle get_status -h"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        self.assertEqual(status, configs['SB_get_status_help'])

    def test_005_cli_verify_cortx_SB_generated_path(self):
        """Validate SB generated path."""
        stdout, stderr, rc = SB_generate_CLI(configs['target_path'], TestSupportBundleCli.cluster_conf_path)
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = stdout.decode('utf-8').split('|')[1].strip()
        bundle_path = stdout.decode('utf-8').split('->')[1].strip()[:-1]
        bundle_path = bundle_path.strip()
        tar_file_name = f"{bundle_path}/{bundle_id}_{Conf.machine_id}.tar.gz"
        self.assertEqual(os.path.exists(tar_file_name), True)

    @classmethod
    def tearDownClass(cls):
        """Test teardown class."""


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        TestSupportBundleCli._cluster_conf_path = sys.argv.pop()
    unittest.main()
