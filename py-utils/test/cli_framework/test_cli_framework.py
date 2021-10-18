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

import unittest
import os
import sys
from cortx.utils.cli_framework.command_factory import CommandFactory
from cortx.utils.cli_framework.command import Output
from cortx.utils.schema import payload
from cortx.utils.schema.providers import  Response

class TestCliFramework(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cli_command=['users', 'show', '-o', '10']
        cls.permissions = {
            'users': { 'list': True, 'update': True, 'create': True }
            }
        cls.directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_data')
        cls.cmd_response = payload.CommonPayload(os.path.join(cls.directory_path, 'users_command_output.json')).load()
        cls.expected_output_file = os.path.join(cls.directory_path, 'users_show_table_output')
        cls.obtained_output_file = os.path.join('/tmp', 'users_show_table_obtained_output')

    def test_command_factory(self):
        self.command = CommandFactory.get_command(self.cli_command, self.permissions, self.directory_path)
        self.assertTrue(self.command.name, 'users')
        self.assertTrue(self.command.sub_command_name, 'show')
        self.assertTrue(self.command.options.get('offset'), 10)

    def test_output(self):
        self.command = CommandFactory.get_command(self.cli_command, self.permissions, self.directory_path)
        response = Response(output=self.cmd_response)
        op = Output(self.command, response)
        with open(self.obtained_output_file, 'w') as obtained_output:
            op.dump(out=obtained_output, err=sys.stderr, response=response,
                        output_type=self.command.options.get('format'),
                        **self.command.options.get('output'))

        with open(self.expected_output_file) as expected_output:
            with open(self.obtained_output_file) as obtained_output:
                self.assertEqual(expected_output.readlines(), obtained_output.readlines())


if __name__ == '__main__':
    unittest.main()
