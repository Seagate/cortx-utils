#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021, 2022 Seagate Technology LLC and/or its Affiliates
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
import errno
from cortx.utils.kv_store import KvStoreFactory
from cortx.utils.kv_store.error import KvError
from cortx.utils.schema.payload import Json
from cortx.utils.conf_store import Conf

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
dir_path = os.path.dirname(os.path.realpath(__file__))
url_config_file = os.path.join(dir_path, 'config.yaml')
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
    loaded_json = ''
    loaded_toml = ''
    loaded_consul = ''
    loaded_yaml = ''
    loaded_ini = ''
    loaded_properties = ''
    loaded_dir = ''
    loaded_dict = ''
    _cluster_conf_path = ''

    @classmethod
    def setUpClass(cls, \
        cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """Setup test class."""
        TestStore.loaded_json = test_current_file('json:///tmp/file.json')
        TestStore.loaded_toml = test_current_file('toml:///tmp/document.toml')
        TestStore.loaded_yaml = test_current_file('yaml:///tmp/sample.yaml')
        TestStore.loaded_ini = test_current_file('ini:///tmp/test.ini')
        TestStore.loaded_properties = test_current_file(
            'properties:///tmp/example.properties')
        TestStore.loaded_dir = test_current_file('dir:///tmp/conf_dir_test')
        TestStore.loaded_dict = test_current_file('dict:{"k1":"v1","k2":''{"k3":"v3", "k4":[25,"v4",27]}}')
        # Get consul endpoints
        if TestStore._cluster_conf_path:
            cls.cluster_conf_path = TestStore._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path
        with open(url_config_file) as fd:
            urls = yaml.safe_load(fd)['conf_url_list']
            endpoint_key = urls['consul_endpoints']
        Conf.load('config', cls.cluster_conf_path, skip_reload=True)
        endpoint_url = Conf.get('config', endpoint_key)
        if endpoint_url is not None and 'http' in endpoint_url:
            url = endpoint_url.replace('http', 'consul')
        else:
            raise KvError(errno.EINVAL, "Invalid consul endpoint key %s", endpoint_key)
        TestStore.loaded_consul = test_current_file(url)

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

    # YAML store
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

    # TOML store
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

    # Ini store
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

    # Properties store
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

    # Dir store
    def test_dir_store_a_by_set_get_kv(self):
        """ Test kv Directory store by setting given key and value """
        TestStore.loaded_dir[0].set(['cluster_uuid'], ['#409'])
        out = TestStore.loaded_dir[0].get(['cluster_uuid'])
        self.assertEqual('#409', out[0])

    def test_dir_store_b_by_get_non_exist_key(self):
        """ Test Kv Directory store to get non exist key, value """
        out = TestStore.loaded_dir[0].get(['non_cluster_uuid'])
        self.assertEqual([None], out)

    def test_dir_store_c_by_set_nested_key(self):
        """ Test Kv Directory store by setting nested key structure """
        TestStore.loaded_dir[0].set(['cluster>cluster_uuid'], ['#409'])
        out = TestStore.loaded_dir[0].get(['cluster>cluster_uuid'])
        self.assertEqual('#409', out[0])

    def test_dir_store_d_by_set_multiple_kv(self):
        """ Test Kv Directory store by setting nested key structure """
        TestStore.loaded_dir[0].set(['cloud>cloud_type', 'kafka>message_type'],
            ['Azure', 'receive'])
        out = TestStore.loaded_dir[0].get(['kafka>message_type'])
        self.assertEqual('receive', out[0])

    def test_dir_store_e_by_delete_multiple_kv(self):
        """ Test Kv Directory store by removing given key using delete api """
        TestStore.loaded_dir[0].delete(['cloud>cloud_type'])
        out = TestStore.loaded_dir[0].get(['cloud>cloud_type'])
        self.assertEqual([None], out)

    # consul store
    # Fix it
    def test_consul_a_set_get_kv(self):
        """ Test consul kv set and get a KV. """
        TestStore.loaded_consul[0].set(['consul_cluster_uuid'], ['#410'])
        out = TestStore.loaded_consul[0].get(['consul_cluster_uuid'])
        self.assertEqual('#410', out[0])

    def test_consul_b_query_unknown_key(self):
        """ Test consul kv query for an absent key. """
        out = TestStore.loaded_consul[0].get(['Wrong_key'])
        self.assertIsNone(out[0])

    def test_consul_store_c_set_nested_key(self):
        """ Test consul kv set a nested key. """
        TestStore.loaded_consul[0].set(['consul_cluster>uuid'], ['#411'])
        out = TestStore.loaded_consul[0].get(['consul_cluster>uuid'])
        self.assertEqual('#411', out[0])

    def test_consul_store_d_set_multiple_kv(self):
        """ Test consul kv by setting nested key structure """
        TestStore.loaded_consul[0].set(['cloud>cloud_type', 'kafka>message_type'],
            ['Azure', 'receive'])
        out1 = TestStore.loaded_consul[0].get(['kafka>message_type'])
        out2 = TestStore.loaded_consul[0].get(['cloud>cloud_type'])
        self.assertEqual('receive', out1[0])
        self.assertEqual('Azure', out2[0])

    def test_consul_store_e_delete_kv(self):
        """ Test consul kv by removing given key using delete api """
        TestStore.loaded_consul[0].delete(['cloud>cloud_type'])
        out = TestStore.loaded_consul[0].get(['cloud>cloud_type'])
        self.assertEqual([None], out)

    # dict store
    def test_001_dict_store_get_data_keys(self):
        """Test dict kv get_data and get_keys."""
        data_out = TestStore.loaded_dict[1].get_data()
        keys_out = TestStore.loaded_dict[1].get_keys(key_index=False)
        expected_data = {'k1': 'v1', 'k2': {'k3': 'v3', 'k4': [25, 'v4', 27]}}
        expected_keys = ['k1', 'k2>k3', 'k2>k4']
        self.assertDictEqual(expected_data, data_out)
        self.assertListEqual(expected_keys, keys_out)

    def test_002_dict_store_set_get_existing_single_kv(self):
        """Test dict kv update existing kv."""
        TestStore.loaded_dict[1].set('k1', 'uv1')
        out = TestStore.loaded_dict[1].get('k1')
        self.assertEqual('uv1', out)

    def test_003_dict_store_set_get_existing_nested_kv(self):
        """Test dict kv update existing nested kv."""
        TestStore.loaded_dict[1].set('k2>k4[0]', '21')
        out = TestStore.loaded_dict[1].get('k2>k4[0]')
        self.assertEqual('21', out)

    def test_004_dict_store_set_get_new_single_kv(self):
        """Test dict kv set and get a KV. """
        TestStore.loaded_dict[1].set('k5', 'v5')
        out = TestStore.loaded_dict[1].get('k5')
        self.assertEqual('v5', out)
        self.assertIn('k5', TestStore.loaded_dict[1].get_keys())

    def test_005_dict_store_set_get_new_nested_kv(self):
        """ Test dict kv set a nested key. """
        TestStore.loaded_dict[1].set('k2>k6', 'v6')
        out = TestStore.loaded_dict[1].get('k2>k6')
        self.assertEqual('v6', out)
        self.assertIn('k2>k6', TestStore.loaded_dict[1].get_keys())

    def test_006_dict_store_delete_single_kv(self):
        """Test dict kv delete kv."""
        TestStore.loaded_dict[1].delete('k1')
        out = TestStore.loaded_dict[1].get('k1')
        self.assertIsNone(out)
        self.assertNotIn('k1', TestStore.loaded_dict[1].get_keys())

    def test_007_dict_store_delete_nested_kv(self):
        """Test dict kv delete nested kv."""
        TestStore.loaded_dict[1].delete('k2>k4[2]')
        out = TestStore.loaded_dict[1].get('k2>k4[2]')
        self.assertIsNone(out)
        self.assertNotIn('k2>k4[2]', TestStore.loaded_dict[1].get_keys())

    def test_008_dict_store_delete_nonexistent_kv(self):
        """Test dict kv delete non-existent kv."""
        delete_out = TestStore.loaded_dict[1].delete('k1>k2>k3')
        self.assertFalse(delete_out)

    def test_009_dict_store_get_nonexistent_kv(self):
        """Test dict kv query for a non-existent key."""
        out = TestStore.loaded_dict[1].get('Wrong_key')
        self.assertIsNone(out)

    def test_010_dict_store_set_empty_value_to_key(self):
        """Test dict kv set empty value to key."""
        TestStore.loaded_dict[1].set('k1', '')
        out = TestStore.loaded_dict[1].get('k1')
        self.assertEqual('', out)

    def test_no_left_shift_kvstore(self):
        """Test and ensure left shift not happening."""
        TestStore.loaded_json[0].set(['bridge>name_list[0]',\
            'bridge>name_list[1]', 'bridge>name_list[2]',
            'bridge>name_list[3]'], ['1', '2', '3', '4'])
        TestStore.loaded_json[0].delete(['bridge>name_list[1]'])
        result_list = TestStore.loaded_json[0].get(['bridge>name_list[1]'])
        self.assertEqual('', result_list[0])

    def test_no_left_shift_end_list_kvstore(self):
        """
        Test and ensure left shift not happening
        while deleting last element of a list
        """
        TestStore.loaded_json[0].set(['bridge>end_name_list[0]',\
            'bridge>end_name_list[1]', 'bridge>end_name_list[2]',\
            'bridge>end_name_list[3]'], ['1', '2', '3', '4'])
        TestStore.loaded_json[0].delete(['bridge>end_name_list[3]'])
        TestStore.loaded_json[0].add_num_keys()
        result_list = TestStore.loaded_json[0].get(['bridge>num_end_name_list'])
        self.assertEqual(result_list[0], 3)


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        TestStore._cluster_conf_path = sys.argv.pop()
    unittest.main()