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

def SB_generate_CLI(comp: str):
    """Executes SB generate CLI command for the given component."""
    cmd = f"support_bundle generate 'sample comment' -c {comp}"
    cmd_proc = SimpleProcess(cmd)
    return cmd_proc.run()

def SB_get_status_CLI(bundle_id: str):
    """Executes SB get_status CLI command for the given bundle_id."""
    cmd = f"support_bundle get_status -b '{bundle_id}'"
    cmd_proc = SimpleProcess(cmd)
    return cmd_proc.run()


class TestSupportBundleCli(unittest.TestCase):

    """Test case will test available API's of Support Bundle."""

    @classmethod
    def setUpClass(cls):
        """Test Setup class."""
        Conf.load('cluster_conf', 'json:///etc/cortx/cluster.conf')
        cls.node_name = Conf.get('cluster_conf', 'cluster>srvnode-1')


    def test_001_cli_verify_SB_generate_single_comp(self):
        """Validate SB generate for single component."""
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)

    def test_002_cli_verify_SB_generate_multi_comp(self):
        """Validate SB generate for multiple components."""
        stdout, stderr, rc = SB_generate_CLI(configs['SB_multi_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(15)

    def test_003_cli_verify_SB_get_status_success_single_comp(self):
        """Validate SB get_status success for single component."""
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(10)
        bundle_id = ''
        #if rc == 0:
        bundle_id = stdout.decode('utf-8').split('|')[1]
        stdout, stderr, rc = SB_get_status_CLI(bundle_id.strip())
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        import ast
        status = ast.literal_eval(status)
        self.assertIsInstance(status, dict)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Success')
            self.assertEqual(status['status'][-1]['result'], 'Success')

    def test_004_cli_verify_get_status_success_multi_comp(self):
        """Validate SB get_status success for multiple components."""
        stdout, stderr, rc = SB_generate_CLI(configs['SB_multi_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(20)
        bundle_id = ''
        #if rc == 0:
        bundle_id = stdout.decode('utf-8').split('|')[1]
        stdout, stderr, rc = SB_get_status_CLI(bundle_id.strip())
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        import ast
        status = ast.literal_eval(status)
        self.assertIsInstance(status, dict)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Success')
            self.assertEqual(status['status'][1]['result'], 'Success')
            self.assertEqual(status['status'][-2]['result'], 'Success')
            self.assertEqual(status['status'][-1]['result'], 'Success')

    def test_005_cli_verify_SB_generate_invalid_comp(self):
        """Validate SB generate for invalid component."""
        stdout, stderr, rc = SB_generate_CLI('util')
        self.assertEqual(rc, 0)
        time.sleep(10)
        bundle_id = ''
        #if rc == 0:
        bundle_id = stdout.decode('utf-8').split('|')[1]
        stdout, stderr, rc = SB_get_status_CLI(bundle_id.strip())
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        import ast
        status = ast.literal_eval(status)
        self.assertIsInstance(status, dict)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')

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
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(10)
        bundle_id = stdout.decode('utf-8').split('|')[1]
        bundle_path = stdout.decode('utf-8').split('->')[1]
        tar_file_name = f"{bundle_id.strip()}_{TestSupportBundleCli.node_name}.tar.gz"
        sb_file_path = f"{(bundle_path.split('.')[0]).strip()}/"\
            f"{bundle_id.strip()}/{TestSupportBundleCli.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)

    def test_009_cli_verify_SB_generate_after_rsyslog_service_stop(self):
        """Validate SB generate while rsyslog service is down."""
        cmd = "systemctl stop rsyslog"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(15)
        bundle_id = stdout.decode('utf-8').split('|')[1]
        bundle_path = stdout.decode('utf-8').split('->')[1]
        tar_file_name = f"{bundle_id.strip()}_{TestSupportBundleCli.node_name}.tar.gz"
        sb_file_path = f"{(bundle_path.split('.')[0]).strip()}/"\
            f"{bundle_id.strip()}/{TestSupportBundleCli.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)
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
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(10)
        bundle_id = stdout.decode('utf-8').split('|')[1]
        bundle_path = stdout.decode('utf-8').split('->')[1]

        tar_file_name = f"{bundle_id.strip()}_{TestSupportBundleCli.node_name}.tar.gz"
        sb_file_path = f"{(bundle_path.split('.')[0]).strip()}/"\
            f"{bundle_id.strip()}/{TestSupportBundleCli.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)
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
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(10)
        bundle_id = stdout.decode('utf-8').split('|')[1]
        bundle_path = stdout.decode('utf-8').split('->')[1]
        tar_file_name = f"{bundle_id.strip()}_{TestSupportBundleCli.node_name}.tar.gz"
        sb_file_path = f"{(bundle_path.split('.')[0]).strip()}/"\
            f"{bundle_id.strip()}/{TestSupportBundleCli.node_name}/{tar_file_name}"
        self.assertEqual(os.path.exists(sb_file_path), True)
        cmd = "pcs cluster start --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        time.sleep(5)

    def test_012_cli_verify_SB_get_status_after_cluster_stop(self):
        """Validate SB get_status while cluster is down."""
        cmd = "pcs cluster stop --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        stdout, stderr, rc = SB_generate_CLI(configs['SB_single_comp'])
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(10)
        bundle_id = stdout.decode('utf-8').split('|')[1]
        stdout, stderr, rc = SB_get_status_CLI(bundle_id.strip())
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        import ast
        status = ast.literal_eval(status)
        self.assertIsInstance(status, dict)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Success')
            self.assertEqual(status['status'][-1]['result'], 'Success')
        cmd = "pcs cluster start --all"
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)
        time.sleep(5)

    def test_013_cli_verify_SB_generate_all_component(self):
        """Validate SB generate for all components."""
        cmd = "support_bundle generate 'sample comment'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        time.sleep(30)

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
