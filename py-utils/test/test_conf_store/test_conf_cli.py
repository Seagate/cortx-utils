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
import subprocess
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
        self.assertEqual(result_data, b'["Homebridge"]\n')

    def test_conf_cli_by_set(self):
        """ Test by setting a value into given key position """
        subprocess.check_output(["conf", "json:///tmp/file1.json", "set",
                                 "bridge>cli_name='client'"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
                                               'get', 'bridge>cli_name'])
        self.assertEqual(result_data, b'["\'client\'"]\n')

    def test_conf_cli_by_get_list(self):
        """ Test by retrieving list of values for given keys seperated by ;"""
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
            'get', 'bridge>name;bridge>lte_type[0]>name'])
        self.assertEqual(result_data, b'["Homebridge", "3g"]\n')

    def test_conf_cli_by_set_list_of_value(self):
        """
        Test by setting list of k,v seperated by ';' semicolon into conf
        """
        subprocess.check_output(["conf", "json:///tmp/file1.json", "set",
            "bridge>cli_name='client';bridge>has_internet='no'"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
            'get', 'bridge>cli_name;bridge>has_internet'])
        self.assertEqual(result_data, b'["\'client\'", "\'no\'"]\n')

    def test_conf_cli_by_delete(self):
        """ Test by deleting a value from the conf """
        subprocess.check_output(["conf", "json:///tmp/file1.json", "delete",
                                 "bridge>port"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
                                               'get', 'bridge>port'])
        self.assertEqual(result_data, b'[null]\n')

    def test_conf_cli_by_format_data(self):
        """ Test by converting data into toml format """
        exp_result = b'- lte_type:\n  - name: 3g\n  - name: 4g\n  ' \
                     b'manufacturer: homebridge.io\n  model: homebridge\n' \
                     b'  name: Homebridge\n  pin: 031-45-154\n' \
                     b'  username: CC:22:3D:E3:CE:30\n\n'
        subprocess.check_output(["conf", "json:///tmp/file1.json", "delete",
                                 "bridge>port"])
        result_data = subprocess.check_output(['conf', 'json:///tmp/file1.json',
                                               'get', 'bridge', '-f', 'yaml'])
        self.assertEqual(result_data, exp_result)

    def test_conf_cli_kv_delim_set(self):
        """
        Test by setting a value into given key position with
        mentioned kv_delim
        """
        set_cmd = "conf json:///tmp/file1.json set -d : cluster>id:093d"
        set_cmd_proc = SimpleProcess(set_cmd)
        set_cmd_proc.run()
        get_cmd = "conf json:///tmp/file1.json get cluster>id"
        get_cmd_proc = SimpleProcess(get_cmd)
        result_data = get_cmd_proc.run()
        self.assertTrue( True if result_data[2]==0 and
            result_data[0]==b'["093d"]\n' else False, result_data[1])

    def test_conf_cli_wrong_kv_delim(self):
        """
        Test by trying to set a value into given key position with
        wrong kv_delim mentioned
        """
        set_cmd = "conf json:///tmp/file1.json set -d : cluster>id=093d"
        set_cmd_proc = SimpleProcess(set_cmd)
        result_data = set_cmd_proc.run()
        self.assertTrue( True if result_data[2]==22 else False)

    def test_conf_cli_invalid_kv_delim(self):
        """
        Test by trying to set a value into given key position with
        invalid kv_delim mentioned
        """
        set_cmd = "conf json:///tmp/file1.json set -d { cluster>id}093d"
        set_cmd_proc = SimpleProcess(set_cmd)
        result_data = set_cmd_proc.run()
        self.assertTrue( True if result_data[2]==22 else False)
    
    def test_conf_cli_multiple_kv_delim(self):
        """
        Test by trying to set a value into given key position with
        multiple kv_delim argument
        """
        set_cmd = "conf json:///tmp/file1.json set -d : : cluster>id:093d"
        set_cmd_proc = SimpleProcess(set_cmd)
        result_data = set_cmd_proc.run()
        self.assertTrue(True if result_data[2]==0 and result_data[0]==b'' else False)
    
    def test_conf_cli_kv_delim_no_value(self):
        """
        Test by trying to set given key with no valu provided
        """
        set_cmd = "conf json:///tmp/file1.json set -d : cluster>id093d"
        set_cmd_proc = SimpleProcess(set_cmd)
        result_data = set_cmd_proc.run()
        self.assertTrue(False if result_data[2]>0 and result_data[0]!=b'' else True)

    def test_conf_cli_multiple_value_split_kv_delim(self):
        """
        Test by setting a value into given key position with multiple 
        value split kv_delim
        """
        set_cmd = "conf json:///tmp/file1.json set -d : cluster>host::localhost"
        set_cmd_proc = SimpleProcess(set_cmd)
        set_cmd_proc.run()
        get_cmd = "conf json:///tmp/file1.json get cluster>host"
        get_cmd_proc = SimpleProcess(get_cmd)
        result_data = get_cmd_proc.run()
        self.assertTrue( True if result_data[2]==0 and
            result_data[0]==b'[":localhost"]\n' else False, result_data[1])

if __name__ == '__main__':

    # create the file and load sample json into it. Start test
    setup_and_generate_sample_files()
    unittest.main()
