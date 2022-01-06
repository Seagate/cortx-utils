#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

from cortx.utils.process import SimpleProcess


class TestIemCli(unittest.TestCase):
    """ Test case will test available API's of IemCli """
    _cluster_conf_path = ''

    @classmethod
    def setUpClass(cls, cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """ Defining commands for test """
        if TestIemCli._cluster_conf_path:
            cls.cluster_conf_path = TestIemCli._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path
        # SEND COMMANDS
        send_cmd = "iem send"
        current_abs_path = os.path.dirname(os.path.abspath(__file__))
        valid_source = "-s 100:200"  # <component_id>:<module_id>
        valid_info = "-i S:X"  # <source_type>:<severity>
        invalid_info = "-i invalid_source:invalid_severity"
        valid_contents = "-c 200:cmd_line_message"  # <event_id>:<message_blob>
        content_file_message = f"-c 200 -f {current_abs_path}/message_file.json"

        cls.send_with_valid_cmdline_args =\
            f"{send_cmd} {valid_source} {valid_info} {valid_contents} --config {TestIemCli.cluster_conf_path}"

        cls.send_with_invalid_cmdline_args =\
            f"{send_cmd} {invalid_info} {valid_source} {valid_contents} --config {TestIemCli.cluster_conf_path}"

        cls.send_with_valid_file_cmdline_args =\
            f"{send_cmd} {valid_source} {valid_info} {content_file_message} --config {TestIemCli.cluster_conf_path}"

        # RECEIVE COMMANDS
        recv_cmd = "iem receive"
        receive_source = "-s 100"  # component_id
        receive_info = "-i S"  # source_type
        invalid_receive_info = "-i invalid_info"
        recv_file_arg = "-f /tmp/iem_receive.log"
        cls.valid_recv = f"{recv_cmd} {receive_source} {receive_info} --config {TestIemCli.cluster_conf_path}"
        cls.valid_recv_log_file = f"{cls.valid_recv} {recv_file_arg} --config {TestIemCli.cluster_conf_path}"
        cls.invalid_recv = f"{recv_cmd} {receive_source} {invalid_receive_info} --config {TestIemCli.cluster_conf_path}"

    @classmethod
    def tearDownClass(cls) -> None:
        """ Runs once after all tests are run """

        SimpleProcess("rm /tmp/iem_receive.log").run()

    # POSITIVE SCENARIOS SEND
    def test_iem_send_with_valid_cmdline_arguments(self):
        cmd = self.send_with_valid_cmdline_args
        import pdb;pdb.set_trace()
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        _, _, rc = result_data  # returns output, error, return code
        self.assertEqual(rc, 0)

    def test_iem_send_with_valid_cmdline_and_message_file(self):
        cmd = self.send_with_valid_file_cmdline_args
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 0)

    # NEGATIVE SCENARIOS SEND
    def test_iem_send_with_invalid_cmdline_argument(self):
        cmd = self.send_with_invalid_cmdline_args
        cmd_proc = SimpleProcess(cmd)
        _, _, rc = cmd_proc.run()
        self.assertEqual(rc, 22)

    # POSITIVE SCENARIO RECEIVE
    def test_iem_receive_with_valid_cmdline_arguments(self):
        # send data to receive
        SimpleProcess(self.send_with_valid_cmdline_args).run()
        cmd = self.valid_recv
        output, _, rc = SimpleProcess(cmd).run()
        self.assertTrue('critical' in output.decode('utf-8'))
        self.assertEqual(rc, 0)

    def test_iem_receive_with_valid_message_file_arguments(self):
        # send data to receive
        SimpleProcess(self.send_with_valid_file_cmdline_args).run()
        cmd = self.valid_recv
        output, _, rc = SimpleProcess(cmd).run()
        self.assertTrue('test_value' in output.decode('utf-8'))
        self.assertEqual(rc, 0)

    def test_iem_receive_output_to_log_file(self):
        # send data to receive
        SimpleProcess(self.send_with_valid_cmdline_args).run()
        cmd = self.valid_recv_log_file
        _, _, rc = SimpleProcess(cmd).run()
        self.assertEqual(rc, 0)
        file_output, _, _ = SimpleProcess("ls /tmp/iem_receive.log").run()
        # Check if file is present
        self.assertTrue('iem_receive.log' in file_output.decode('utf-8'))
        # Check if an expected word is present in file
        with open('/tmp/iem_receive.log') as fd:
            data = ' '.join(fd.readlines())
            self.assertTrue('cmd_line_message' in data)

    # NEGATIVE SCENARIO RECEIVE
    def test_iem_receive_with_invalid_cmdline_arguments(self):
        cmd = self.invalid_recv
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        _, _, rc = result_data
        self.assertEqual(rc, 2)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        TestIemCli._cluster_conf_path = sys.argv.pop()
    unittest.main()