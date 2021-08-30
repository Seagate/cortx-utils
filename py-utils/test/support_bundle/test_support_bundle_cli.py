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


import unittest
from cortx.utils.process import SimpleProcess


class TestSupportBundleCli(unittest.TestCase):

    """Test case will test available API's of Support Bundle."""

    def test_001generate_1_component(self):
        cmd = "support_bundle generate 'sample comment' -c 'provisioner'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)

    def test_002generate_multiple_component(self):
        cmd = "support_bundle generate 'sample comment' -c 'csm;provisioner'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)

    def test_003generate_all_component(self):
        cmd = "support_bundle generate 'sample comment'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)

    def test_004get_status_success(self):
        cmd = "support_bundle generate 'sample comment' -c 'provisioner'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        bundle_id = ''
        if rc == 0:
            bundle_id = stdout.decode('utf-8').split('|')[1]
        cmd = f"support_bundle get_status -b '{bundle_id.strip()}'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        import ast
        status = ast.literal_eval(status)
        self.assertIsInstance(status, dict)
    
    def test_005_wrong_comp(self):
        cmd = "support_bundle generate 'sample comment' -c 'util'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        bundle_id = ''
        if rc != 0:
            cmd = f"support_bundle get_status -b '{bundle_id.strip()}'"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, rc = cmd_proc.run()
        self.assertIsInstance(stdout, bytes)
        self.assertEqual(stderr, b'')
        self.assertEqual(rc, 0)
        status = stdout.decode('utf-8')
        import ast
        status = ast.literal_eval(status)
        self.assertIsInstance(status, dict)
        if status['status']:
            self.assertEqual(status['status'][0]['result'], 'Error')


if __name__ == '__main__':
    unittest.main()

