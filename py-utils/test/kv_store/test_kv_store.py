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
from __future__ import absolute_import
import os
import sys
import unittest
import yaml, json, toml, configparser
from conf_sample_json import sample_config

from cortx.utils.kv_store.kv_store_factory import KvStoreFactory

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

def setup_and_generate_sample_files():
    """ This function will generate all required types of file """

    with open(r'/tmp/file.json', 'w+') as file:
        json.dump(sample_config, file,indent=2  )

    with open(r'/tmp/sample.yaml', 'w+') as file:
        yaml.dump(sample_config, file)

    with open(r'/tmp/document.toml', 'w+') as file:
        toml.dump(sample_config, file)

    p_config = configparser.ConfigParser()
    p_config.read_dict(sample_config)
    with open(r'/tmp/test.ini', 'w+') as file:
        p_config.write(file)

def test_current_file(file_path):
    kv_store = KvStoreFactory.get_instance(file_path)
    data = kv_store.load()
    return [kv_store, data]

class TestStore(unittest.TestCase):

    loaded_json = test_current_file('json:///tmp/file.json')
    loaded_yaml = test_current_file('yaml:///tmp/sample.yaml')
    loaded_toml = test_current_file('toml:///tmp/document.toml')
    loaded_ini = test_current_file('ini:///tmp/test.ini')

    def test_json_file(self):
        """Test Kv JSON store. load json store from json:///tmp/file.json"""
        import ipdb;ipdb.set_trace()
        result_data = TestStore.loaded_json[1]
        self.assertEqual(result_data, sample_config)

    def test_json_file_get(self):
        """Test Kv JSON store by retrieving value of given key from the jsonstore"""
        result_data = TestStore.loaded_json[0].get(['bridge.name'])
        self.assertEqual(result_data[0], 'Homebridge')

    def test_json_file_set(self):
        """Test kv JSON store by setting the value of given key, value to the jsonstore"""
        TestStore.loaded_json[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_json[0].get(['user'])
        self.assertEqual(result_data[0], 'kvstore')

    def test_json_delete(self):
        """Test kv JSON store by removing given key and its value from jsonstore"""
        TestStore.loaded_json[0].delete(['user'])
        result_data = TestStore.loaded_json[0].load()
        self.assertTrue( True if 'user' not in result_data else False, "Test case failed")

    # YAML starts
    def test_yaml_file_load(self):
        """Test Kv YAML store. load yaml store from yaml:///tmp/sample.toml"""
        result_data = TestStore.loaded_yaml[1]
        self.assertEqual(result_data, sample_config)

    def test_yaml_get(self):
        """Test Kv YAML store by retrieving value of given key from the yamlstore"""
        result_data = TestStore.loaded_yaml[0].get(['bridge.model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_yaml_set(self):
        """Test kv YAML store by setting the value of given key, value to the yamlstore"""
        TestStore.loaded_yaml[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_yaml[0].get(['user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_yaml_delete(self):
        """Test kv YAML store by removing given key and its value from yamlstore"""
        TestStore.loaded_yaml[0].delete(['user'])
        result_data = TestStore.loaded_yaml[0].load()
        self.assertTrue(True if 'user' not in result_data else False, "Test case failed")

    # TOML starts
    def test_toml_file_load(self):
        """Test Kv TOML store. load toml store from toml:///tmp/document.toml"""
        result_data = TestStore.loaded_toml[1]
        self.assertEqual(result_data, sample_config)

    def test_toml_get(self):
        """Test Kv toml store by retrieving value of given key from the tomlstore"""
        result_data = TestStore.loaded_toml[0].get(['bridge.model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_toml_set(self):
        """Test kv TOML store by setting the value of given key, value to the tomlstore"""
        TestStore.loaded_yaml[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_toml[0].get(['user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_toml_delete(self):
        """Test kv TOML store by removing given key and its value from tomlstore"""
        TestStore.loaded_yaml[0].delete(['user'])
        result_data = TestStore.loaded_toml[0].load()
        self.assertTrue(True if 'user' not in result_data else False, "Test case failed")

    # Ini starts
    def test_ini_file_load(self):
        """Test Kv INI store. load ini store from ini:///tmp/document.ini"""
        result_data = {s: dict(TestStore.loaded_ini[1].items(s)) for s in
                                 TestStore.loaded_ini[1].sections()}
        # result_data = dict(TestStore.loaded_ini[1]._sections)
        # self.assertEqual(result_data, sample_config)
        self.assertTrue(True if result_data == sample_config else False)

    def test_ini_get(self):
        """Test Kv INI store by retrieving value of given key from the inistore"""
        result_data = TestStore.loaded_ini[0].get(['bridge.model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_ini_set(self):
        """Test kv INI store by setting the value of given key, value to the inistore"""
        TestStore.loaded_yaml[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_ini[0].get(['user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_ini_delete(self):
        """Test kv INI store by removing given key and its value from inistore"""
        TestStore.loaded_yaml[0].delete(['user'])
        result_data = TestStore.loaded_ini[0].load()
        self.assertTrue(True if 'user' not in result_data else False, "Test case failed")

if __name__ == '__main__':
    # setup_and_generate_sample_files()
    unittest.main()