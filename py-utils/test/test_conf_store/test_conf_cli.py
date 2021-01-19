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

import json
import os
import sys
import unittest
from cortx.utils.process import SimpleProcess

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from cortx.utils.schema.payload import Json

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_conf_sample_json.json')
sample_config = Json(file_path).load()


def setup_and_generate_sample_files():
    """ This function will generate all required types of file """
    with open(r'/tmp/file1.json', 'w+') as file:
        json.dump(sample_config, file, indent=2)


class TestConfCli(unittest.TestCase):
    """Test case will test available API's of ConfStore"""

    def test_conf_cli_by_get(self):
        """ Test by retrieving a value using get api """
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
                                               'get', 'bridge>name'])
        escapes = ''.join([chr(char) for char in range(1, 32)])
        translator = str.maketrans('', '', escapes)
        result_data = result_data.decode().translate(translator)
        self.assertEqual(result_data, "Homebridge")

    def test_conf_cli_by_set(self):
        """ Test by setting a value into given key position """
        subprocess.check_output(["conf", "json:///tmp/file1.json", "set",
                                 "bridge>cli_name='client'"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
                                               'get', 'bridge>cli_name'])
        escapes = ''.join([chr(char) for char in range(1, 32)])
        translator = str.maketrans('', '', escapes)
        result_data = result_data.decode().translate(translator)
        self.assertEqual(result_data, "client")

    def test_conf_cli_by_get_list(self):
        """ Test by retrieving list of values for given keys seperated by ;"""
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
            'get', 'bridge>name;bridge>lte_type[0]>name'])
        result_data = result_data.decode().split('\n')
        self.assertListEqual(result_data, ['Homebridge', '3g', ''])

    def test_conf_cli_by_set_list_of_value(self):
        """
        Test by setting list of k,v seperated by ';' semicolon into conf
        """
        subprocess.check_output(["conf", "json:///tmp/file1.json", "set",
            "bridge>cli_name='client';bridge>has_internet='no'"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
            'get', 'bridge>cli_name;bridge>has_internet'])
        result_data = result_data.decode().split('\n')
        self.assertListEqual(result_data, ['client', 'no', ''])

    def test_conf_cli_by_delete(self):
        """ Test by deleting a value from the conf """
        subprocess.check_output(["conf", "json:///tmp/file1.json", "delete",
                                 "bridge>port"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
                                               'get', 'bridge>port'])
        escapes = ''.join([chr(char) for char in range(1, 32)])
        translator = str.maketrans('', '', escapes)
        result_data = result_data.decode().translate(translator)
        self.assertEqual(result_data, "None")


if __name__ == '__main__':

    # create the file and load sample json into it. Start test
    setup_and_generate_sample_files()
    unittest.main()
