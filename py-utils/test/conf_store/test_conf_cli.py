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
properties_file = os.path.join(dir_path, 'properties.txt')
sample_config = Json(file_path).load()


def setup_and_generate_sample_files():
    """ This function will generate all required types of file """
    with open(r'/tmp/file1.json', 'w+') as file:
        json.dump(sample_config, file, indent=2)

    with open(r'/tmp/example.properties', 'w+') as file:
        sample_config.update(sample_config['bridge'])
        for key, val in sample_config.items():
            file.write("%s = %s\n" %(key, val))
        # below list contains other scenarios which need be handled
        lines = ["k=v\n", " #This is second line\n",
            "# This is sample comment\n", "\n", "k=v1=v2#\n", "k = v1 = v2\n",
            "#This is another sample comment without EOL", "    #", "   #  "]
        for each in lines:
            file.write(each)

    with open(r'/tmp/file2.json', 'w+') as file:
        sample_config['version'] = '2.0.1'
        sample_config['branch'] = 'stable'
        json.dump(sample_config, file, indent=2)


def delete_files():
    files = ['/tmp/file1.json', '/tmp/file2.json']
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except OSError as e:
            print(e)


class TestConfCli(unittest.TestCase):
    """Test case will test available API's of ConfStore"""

    @classmethod
    def setUpClass(cls):
        setup_and_generate_sample_files()

    def test_conf_cli_by_get(self):
        """ Test by retrieving a value using get api """
        cmd = "conf json:///tmp/file1.json get bridge>name"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertTrue(True if result_data[2] == 0 and
            result_data[0] == b'["Homebridge"]\n' else False, result_data[1])

    def test_conf_cli_by_get_diff(self):
        """ Test by retrieving a value using get api """
        cmd = "conf json:///tmp/file1.json diff json:///tmp/file2.json -k version;branch"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertTrue(True if result_data[2] == 0 and
            result_data[0] == b'1c1\n< [2.0.0, main]\n---\n> [2.0.1, stable]\n\n' else False, result_data[1])

    def test_conf_cli_by_set(self):
        """ Test by setting a value into given key position """
        cmd_1 = "conf json:///tmp/file1.json set bridge>cli_name='client'"
        cmd_proc_1 = SimpleProcess(cmd_1)
        cmd_proc_1.run()
        cmd_2 = "conf json:///tmp/file1.json get bridge>cli_name"
        cmd_proc_2 = SimpleProcess(cmd_2)
        result_data = cmd_proc_2.run()
        self.assertTrue(True if result_data[2]==0 and
            result_data[0]==b'["\'client\'"]\n' else False, result_data[1])

    def test_conf_cli_by_get_list(self):
        """ Test by retrieving list of values for given keys seperated by ;"""
        cmd = "conf json:///tmp/file1.json get bridge>name;bridge>lte_type[0]>name"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertTrue(True if result_data[2]==0 and
            result_data[0]==b'["Homebridge", "3g"]\n' else False, result_data[1])

    def test_conf_cli_by_set_list_of_value(self):
        """
        Test by setting list of k,v seperated by ';' semicolon into conf
        """
        cmd_1 = "conf json:///tmp/file1.json set bridge>cli_name='client';" \
                "bridge>has_internet='no'"
        cmd_proc_1 = SimpleProcess(cmd_1)
        cmd_proc_1.run()
        cmd_2 = "conf json:///tmp/file1.json get bridge>cli_name;" \
                "bridge>has_internet"
        cmd_proc_2 = SimpleProcess(cmd_2)
        result_data = cmd_proc_2.run()
        self.assertTrue(True if result_data[2] == 0 and
            result_data[0] == b'["\'client\'", "\'no\'"]\n'
            else False, result_data[1])

    def test_conf_cli_by_delete(self):
        """ Test by deleting a value from the conf """
        cmd_1 = "conf json:///tmp/file1.json delete 'bridge>port'"
        cmd_proc_1 = SimpleProcess(cmd_1)
        cmd_proc_1.run()
        cmd_2 = "conf json:///tmp/file1.json get 'bridge>port'"
        cmd_proc_2 = SimpleProcess(cmd_2)
        result_data = cmd_proc_2.run()
        self.assertTrue(True if result_data[2] == 0 and
            result_data[0]==b'[null]\n' else False, result_data[1])

    def test_conf_cli_by_format_data(self):
        """ Test by converting data into toml format """
        exp_result = b'- lte_type:\n  - name: 3g\n  - name: 4g\n  ' \
                     b'manufacturer: homebridge.io\n  model: homebridge\n' \
                     b'  name: Homebridge\n  pin: 031-45-154\n' \
                     b'  username: CC:22:3D:E3:CE:30\n\n'
        cmd_1 = "conf json:///tmp/file1.json delete bridge>port"
        cmd_proc_1 = SimpleProcess(cmd_1)
        cmd_proc_1.run()
        cmd_2 = "conf json:///tmp/file1.json get bridge -f yaml"
        cmd_proc_2 = SimpleProcess(cmd_2)
        result_data = cmd_proc_2.run()
        self.assertTrue(True if result_data[2]==0 and
            result_data[0]==exp_result else False, result_data[1])

    # Properties store test case starts here
    def test_conf_cli_by_get_from_properties_store(self):
        """ Test by retrieving a value from properties store using get api """
        cmd = "conf properties:///tmp/example.properties get name"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertTrue(True if result_data[2] == 0 and result_data[0] ==
            b'["Homebridge"]\n' else False, result_data[1])

    def test_conf_cli_by_set_to_properties_store(self):
        """ Test by setting a value to properties store using set api """
        cmd_1 = "conf properties:///tmp/example.properties set age=27;" \
                "contact=789654112"
        cmd_proc_1 = SimpleProcess(cmd_1)
        cmd_proc_1.run()
        cmd_2 = "conf properties:///tmp/example.properties get age"
        cmd_proc_2 = SimpleProcess(cmd_2)
        result_data = cmd_proc_2.run()
        self.assertTrue(True if result_data[2] == 0 and
            result_data[0] == b'["27"]\n' else False, result_data[1])

    def test_conf_cli_by_wrong_file_format_properties_store(self):
        """ Test by wrong file with properties store """
        cmd = "conf properties:///tmp/file1.json get ssh_host"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertEqual(result_data[2], 22)

    def test_conf_cli_by_empty_str_properties_store(self):
        """ Test by setting an empty value to propertiesStore using set api """
        cmd_1 = "conf properties:///tmp/example.properties set ssh_host="
        cmd_proc_1 = SimpleProcess(cmd_1)
        cmd_proc_1.run()
        cmd_2 = "conf properties:///tmp/example.properties get ssh_host"
        cmd_proc_2 = SimpleProcess(cmd_2)
        result_data = cmd_proc_2.run()
        self.assertTrue(False if result_data[0]!=b'[""]\n' and result_data[0]>0
                        else True)

    def test_conf_cli_by_wrong_file_store(self):
        """ Test by trying to load wrong json file for properties protocol """
        try:
            cmd = "conf properties:///tmp/file1.json get ssh_host"
            cmd_proc = SimpleProcess(cmd)
            cmd_proc.run()
        except Exception as err:
            exit_code = 22
            self.assertEqual(err.args[0], exit_code)

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

    def test_conf_cli_with_kv_delim_in_value(self):
        """
        Test by setting a value into given key position with value
        contains kv_delim
        """
        set_cmd = "conf json:///tmp/file1.json set -d : cluster>host:localhost:9090"
        set_cmd_proc = SimpleProcess(set_cmd)
        set_cmd_proc.run()
        get_cmd = "conf json:///tmp/file1.json get cluster>host"
        get_cmd_proc = SimpleProcess(get_cmd)
        result_data = get_cmd_proc.run()
        self.assertTrue( True if result_data[2]==0 and
            result_data[0]==b'["localhost:9090"]\n' else False, result_data[1])

    def test_conf_cli_properties_wrong_format_kv(self):
        """
        Test by reading invalid k#V format key value and validate
        the result error message
        """
        with open(r'/tmp/example_invalid.properties', 'w+') as file:
            file.write("key1#val1")
        cmd = "conf properties:///tmp/example_invalid.properties get name"
        cmd_proc = SimpleProcess(cmd)
        try:
            result_data = cmd_proc.run()
        except Exception:
            self.assertEqual(result_data[2], '22')

    def test_conf_cli_merge_keys(self):
        cmd = "conf json:///tmp/file1.json merge json:///tmp/file2.json -k version;branch"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertEqual(result_data[2], 0)

    def test_conf_cli_merge(self):
        cmd = "conf json:///tmp/file1.json merge json:///tmp/file2.json"
        cmd_proc = SimpleProcess(cmd)
        result_data = cmd_proc.run()
        self.assertEqual(result_data[2], 0)

    @classmethod
    def tearDownClass(cls):
        delete_files()


if __name__ == '__main__':
    # create the file and load sample json into it. Start test
    setup_and_generate_sample_files()
    unittest.main()

