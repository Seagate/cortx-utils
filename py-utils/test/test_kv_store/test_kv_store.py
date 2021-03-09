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
import configparser
import json
import toml
import yaml
from cortx.utils.kv_store import KvStoreFactory
from cortx.utils.schema.payload import Json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'conf_sample_json.json')
properties_file = os.path.join(dir_path, 'properties.txt')
sample_config = Json(file_path).load()


def setup_and_generate_sample_files():
    """ This function will generate all required types of file """

    with open(r'/tmp/file.json', 'w+') as file:
        json.dump(sample_config, file, indent=2)

    with open(r'/tmp/sample.yaml', 'w+') as file:
        yaml.dump(sample_config, file)

    with open(r'/tmp/document.toml', 'w+') as file:
        toml.dump(sample_config, file)

    p_config = configparser.ConfigParser()
    p_config.read_dict(sample_config)
    with open(r'/tmp/test.ini', 'w+') as file:
        p_config.write(file)

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

# This function should be executed before testcase class
setup_and_generate_sample_files()


def test_current_file(file_path):
    kv_store = KvStoreFactory.get_instance(file_path)
    data = kv_store.load()
    return [kv_store, data]


class TestStore(unittest.TestCase):
    loaded_json = test_current_file('json:///tmp/file.json')
    loaded_toml = test_current_file('toml:///tmp/document.toml')
    loaded_yaml = test_current_file('yaml:///tmp/sample.yaml')
    loaded_ini = test_current_file('ini:///tmp/test.ini')
    loaded_properties = test_current_file(
        'properties:///tmp/example.properties')

    def test_json_file(self):
        """Test Kv JSON store. load json store from json:///tmp/file.json"""
        result_data = TestStore.loaded_ini[1].get('bridge>name')
        self.assertTrue(result_data, 'Homebridge')

    def test_json_file_get(self):
        """
        Test Kv JSON store by retrieving value of given key from the jsonstore
        """
        result_data = TestStore.loaded_json[0].get(['bridge>port'])
        self.assertEqual(result_data[0], 51826)

    def test_json_file_set(self):
        """
        Test kv JSON store by setting the value of given key, value to the
        jsonstore
        """
        TestStore.loaded_json[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_json[0].get(['user'])
        self.assertEqual(result_data[0], 'kvstore')

    def test_json_delete(self):
        """
        Test kv JSON store by removing given key and its value from jsonstore
        """
        TestStore.loaded_json[0].delete(['bridge>name'])
        result_data = TestStore.loaded_json[0].get(['bridge>name'])
        self.assertEqual(result_data[0], None)

    # YAML starts
    def test_yaml_file_load(self):
        """Test Kv YAML store. load yaml store from yaml:///tmp/sample.toml"""
        result_data = TestStore.loaded_yaml[0].get(['bridge>model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_yaml_get(self):
        """
        Test Kv YAML store by retrieving value of given key from the yamlstore
        """
        result_data = TestStore.loaded_yaml[0].get(['bridge>model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_yaml_set(self):
        """
        Test kv YAML store by setting the value of given key, value to the
        yamlstore"""
        TestStore.loaded_yaml[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_yaml[0].get(['user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_yaml_delete(self):
        """Test kv YAML store by removing given key and its value from
        yamlstore"""
        TestStore.loaded_yaml[0].delete(['bridge>port'])
        result_data = TestStore.loaded_yaml[0].get(['bridge>port'])
        self.assertEqual(result_data[0], None)

    # TOML starts
    def test_toml_file_load(self):
        """Test Kv TOML store. load toml store from toml:///tmp/document.toml"""
        result_data = TestStore.loaded_toml[1].get('bridge>model')
        self.assertEqual(result_data, "homebridge")

    def test_toml_get(self):
        """Test Kv toml store by retrieving value of given key from the
        tomlstore"""
        result_data = TestStore.loaded_toml[0].get(['bridge>model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_toml_by_set(self):
        """Test kv TOML store by setting the value of given key, value to the
        tomlstore"""
        TestStore.loaded_toml[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_toml[0].get(['user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_toml_delete(self):
        """Test kv TOML store by removing given key and its value from
        tomlstore"""
        TestStore.loaded_toml[0].delete(['user'])
        result_data = TestStore.loaded_toml[0].get(['user'])
        self.assertEqual(result_data[0], None)

    # Ini starts
    def test_ini_file_load(self):
        """Test Kv INI store. load ini store from ini:///tmp/document.ini"""
        result_data = TestStore.loaded_ini[1].get('bridge>name')
        self.assertTrue(True if result_data == 'Homebridge' else False)

    def test_ini_get(self):
        """Test Kv INI store by retrieving value of given key from the
        inistore"""
        result_data = TestStore.loaded_ini[0].get(['bridge>model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_ini_by_set(self):
        """Test kv INI store by setting the value of given key, value to the
        inistore"""

        TestStore.loaded_ini[0].set(['bridge>user'], ['kvstore'])
        result_data = TestStore.loaded_ini[0].get(['bridge>user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_ini_delete(self):
        """Test kv INI store by removing given key and its value from
        inistore"""
        TestStore.loaded_ini[0].delete(['bridge>user'])
        try:
            TestStore.loaded_ini[0].get(['bridge>user'])
        except Exception as err:
            self.assertTrue('user' in err.args)

    def test_kv_format_yaml_to_json(self):
        """Test Kv format converter functionality store.
        load yaml store from yaml:///tmp/sample.toml"""
        result_data = TestStore.loaded_yaml[0].get_data('json')
        self.assertTrue(result_data,
            '{"bridge": {"manufacturer": "homebridge.io", "model": '
            '"homebridge","name": "Homebridge", "pin": "031-45-154", '
            '"port": 51826, "username": "CC:22:3D:E3:CE:30"}}')

    # Properties starts
    def test_properties_file_load(self):
        """
        Test Kv Properties store. load properties store from
        properties:///tmp/example.properties
        """
        result_data = TestStore.loaded_properties[1].get('model')
        self.assertEqual(result_data, "homebridge")

    def test_properties_get(self):
        """
        Test Kv properties store by retrieving value of given key from the
        propertiesstore
        """
        result_data = TestStore.loaded_properties[0].get(['model'])
        self.assertEqual(result_data[0], "homebridge")

    def test_properties_by_set(self):
        """
        Test kv Properties store by setting the value of given key, value to the
        propertiesstore
        """
        TestStore.loaded_properties[0].set(['user'], ['kvstore'])
        result_data = TestStore.loaded_properties[0].get(['user'])
        self.assertEqual(result_data[0], "kvstore")

    def test_properties_by_set_empty_string(self):
        """
        Test kv Properties store by setting the empty value for the given
        key to the propertiesstore
        """
        TestStore.loaded_properties[0].set(['empty_value'], [''])
        result_data = TestStore.loaded_properties[0].get(['empty_value'])
        self.assertEqual(result_data[0], "")

    def test_properties_by_set_eq_sp(self):
        """
        Test kv Properties store by setting the value of given key, value to the
        propertiesstore
        """
        TestStore.loaded_properties[0].set(['location'], ['in'])
        result_data = TestStore.loaded_properties[0].get(['location'])
        self.assertEqual(result_data[0], "in")

    def test_properties_delete(self):
        """
        Test kv Properties store by removing given key and its value from
        propertiesstore
        """
        TestStore.loaded_properties[0].delete(['user'])
        result_data = TestStore.loaded_properties[0].get(['user'])
        self.assertEqual(result_data[0], None)

    def test_properties_non_exist_key_delete(self):
        """
        Test kv Properties store by trying to remove given key and its value
        from which is not available in propertiesstore
        """
        TestStore.loaded_properties[0].delete(['user'])
        result_data = TestStore.loaded_properties[0].get(['user'])
        self.assertEqual(result_data[0], None)

    def test_properties_set_with_multiple_eq(self):
        """
        Test kv Properties store by setting the value of given key, value to the
        propertiesstore
        """
        TestStore.loaded_properties[0].set(['test_ml_eq'], ['=kv = store'])
        try:
            TestStore.loaded_properties[0].get(['user'])
        except Exception as err:
            self.assertEqual('Invalid properties store format %s. %s.', err.args[1])

    def test_properties_protocol_with_yamlfile(self):
        """
        Test kv Properties store by setting the value of given key, value to the
        propertiesstore
        """
        try:
            test_current_file('properties:///tmp/sample.yaml')
        except Exception as err:
            self.assertEqual('Invalid properties store format %s. %s.', err.args[1])

    def test_properties_with_invalid_kv_format_delim(self):
        """
        Test kv Properties store by accessing wrong kv format
        key#value invalid - should be key=value
        """
        with open(r'/tmp/example_invalid.properties', 'w+') as file:
            file.write("key1#val1")
        try:
            test_current_file('properties:///tmp/example_invalid.properties')
        except Exception as err:
            exp_err='Invalid properties store format key1#val1. not enough '\
            'values to unpack (expected 2, got 1).'
            self.assertEqual(exp_err, err._desc)

    def test_kv_pillar_support(self):
        """ Test Kv Store with pillar data by loading it to KvStore """
        kv_store = KvStoreFactory.get_instance("pillar://930404:Seagate#123@127.0.0.1")
        data = kv_store.load()
        self.assertGreaterEqual(len(data.get_keys()), 0)

    def test_kv_pillar_set_target(self):
        """ Test Kv Store with pillar data by setting targeted minions """
        kv_store = KvStoreFactory.get_instance("pillar://930404:Seagate#123@127.0.0.1")
        kv_store.set_target('srvnode-1')
        self.assertEqual(kv_store._target, 'srvnode-1')

    def test_kv_pillar_get_api(self):
        """ Test Kv Store with pillar data by getting value for key """
        kv_store = KvStoreFactory.get_instance("pillar://930404:Seagate#123@127.0.0.1")
        kv_inst = kv_store.load()
        data = kv_inst.get_data()
        # To get the key for testing dynamically 
        # since pillar store data unknown on other system
        key1 = list(data.keys())[0]
        key2_list = list(data[key1].keys())
        if len(key2_list) > 0:
            out = kv_inst.get(key2_list[0])
            out = list(out.values())
            result = data[key1][key2_list[0]]
            self.assertEqual(out[0], result)
        else:
            #Consider your pillar has no values
            self.assertTrue(True if len(key2)==0 else False)

    def test_kv_pillar_dump_api_test(self):
        """ 
        Test Kv Store with pillar data by dump pillar data into a file 
        dump file default location
        /tmp/pillar_store.json
        """
        kv_store = KvStoreFactory.get_instance("pillar://930404:Seagate#123@127.0.0.1")
        data = kv_store.load()
        kv_store.dump(data)
        ret_json = test_current_file("json:///tmp/pillar_store.json")
        result = ret_json[1].get_data()
        self.assertTrue(result)
    
    def test_kv_pillar_dump_api_custom_location_test(self):
        """ 
        Test Kv Store with pillar data by dump pillar data into a file 
        dump file custom location
        /tmp/cust_pillar_bkup.json
        """
        kv_store = KvStoreFactory.get_instance("pillar://930404:Seagate#123@127.0.0.1")
        data = kv_store.load()
        kv_store.dump(data, "/tmp/cust_pillar_bkup.json")
        ret_json = test_current_file("json:///tmp/cust_pillar_bkup.json")
        result = ret_json[1].get_data()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
