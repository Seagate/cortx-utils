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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from cortx.utils.schema.payload import Json
from cortx.utils.conf_store import Conf
from cortx.utils.schema.format import Format
from cortx.utils.kv_store.error import KvError


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

    # create conf sample for conf merge
    Conf.load('merge_index', 'yaml:///tmp/test_conf_merge.conf.sample')
    Conf.set('merge_index', 'cortx>software>common>message_bus_type', 'kafka')
    Conf.save('merge_index')


def load_config(index, backend_url):
    """Instantiate and Load Config into constore"""
    Conf.load(index, backend_url)
    return Conf


def delete_files():
    files = ['/tmp/test_conf_merge.conf.sample', '/tmp/test_conf_merge.conf']
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except OSError as e:
            print(e)


class TestConfStore(unittest.TestCase):
    """Test case will test available API's of ConfStore"""

    @classmethod
    def setUpClass(cls):
        setup_and_generate_sample_files()
        Conf.load('src_index', 'yaml:///tmp/test_conf_merge.conf.sample')
        Conf.load('dest_index', 'yaml:///tmp/test_conf_merge.conf')
        dict_data = {'k1': 'v1', 'k2': {'k3': 'v3', 'k4': {'k5': \
            [25,'v5',27], 'k6': {'k7': 'v7', 'k8': 'v8'}}}}
        dict_json = Format.dump(dict_data,"json")
        Conf.load('dict', "dict:"+dict_json)

    def test_json_message_kv_store(self):
        """Tests jsonmessage basic operation."""
        index = 'json_message_kv_store_index'
        Conf.load(index, 'jsonmessage:{"key1":"val1"}')
        self.assertEqual(Conf.get(index, 'key1'), 'val1')
        Conf.set(index, 'key2', 'val2')
        self.assertEqual(Conf.get_keys(index),['key1', 'key2'])
        Conf.set(index, 'key2>key3>key4', 'val4')
        Conf.delete(index, 'key2>key3>key4')
        self.assertEqual(Conf.get(index, 'key2>key3>key4'), None)
        # TODO: Add delete cases when confStore branch is merged
        # and force option is available




    def test_conf_store_load_and_get(self):
        """Test by loading the give config file to in-memory"""
        load_config('sspl_local', 'json:///tmp/file1.json')
        result_data = Conf.get_keys('sspl_local')
        self.assertTrue('bridge>name' in result_data)

    def test_conf_store_get_by_index_with_single_key(self):
        """Test by getting the key from the loaded config"""
        load_config('msg_local', 'json:///tmp/file1.json')
        result_data = Conf.get('msg_local', 'bridge')
        self.assertTrue(True if 'name' in result_data else False)

    def test_conf_store_get_by_index_with_chained_key(self):
        """
        Test by getting the chained key(key1.key2.key3) from the loaded config
        """
        load_config('test_local', 'json:///tmp/file1.json')
        result_data = Conf.get('test_local', 'bridge>name')
        self.assertEqual(result_data, 'Homebridge')

    def test_conf_store_get_wrong_key(self):
        """Test by trying to get the wrong key from the loaded config"""
        load_config('new_local', 'json:///tmp/file1.json')
        result_data = Conf.get('test_local', 'bridge>no_name_field')
        self.assertEqual(result_data, None)

    def test_conf_store_set(self):
        """
        Test by setting the key, value to given index and reading it back.
        """
        load_config('set_local', 'json:///tmp/file1.json')
        Conf.set('set_local', 'bridge>proxy', 'no')
        result_data = Conf.get('set_local', 'bridge>proxy')
        self.assertEqual(result_data, 'no')

    def test_conf_store_get_keys(self):
        """Test listing all available keys for given index"""
        load_config('get_keys_local', 'json:///tmp/file1.json')
        result_data = Conf.get_keys('get_keys_local')
        self.assertTrue(True if 'bridge>name' in result_data else False)

    def test_get_keys_delete(self):
        """Test get_keys after deletion of a key."""
        load_config('get_keys_delete', 'json:///tmp/file1.json')
        Conf.set('get_keys_delete', 'bridge>delete>key', 'del_val')
        pre_key_list = Conf.get_keys('get_keys_delete')
        Conf.delete('get_keys_delete', 'bridge>delete>key')
        post_key_list = Conf.get_keys('get_keys_delete')
        self.assertTrue( pre_key_list != post_key_list )

    def test_conf_store_delete(self):
        """
        Test by removing the key, value to given index and reading it back.
        """
        load_config('delete_local', 'json:///tmp/file1.json')
        Conf.delete('delete_local', 'bridge>proxy')
        result_data = Conf.get('delete_local', 'bridge>proxy')
        self.assertEqual(result_data, None)

    def test_conf_store_a_backup_and_save_a_copy(self):
        """Test by creating a backup file and copying then saving it back."""
        conf_file = 'json:/tmp/file1.json'
        load_config('csm_local', conf_file)
        Conf.load('backup', f"{conf_file}.bak")
        Conf.copy('csm_local', 'backup')
        Conf.save('backup')
        result_data = Conf.get_keys('backup', key_index=True)
        # Expected list should match the result_data list output
        expected_list = Conf.get_keys('csm_local')
        self.assertListEqual(sorted(expected_list), sorted(result_data))
        # Expected Length should match else Failure.
        self.assertTrue(True if len(expected_list) == len(result_data) else False)

    def test_conf_load_invalid_arguments(self):
        """
        Test by passing invalid argument to confstore load -invalid case
        """
        try:
            Conf.load('invalid_arg', 'json:/tmp/file1.json',
                      test_arg='This is invalid')
        except Exception as err:
            self.assertTrue(True if err.args[1] == "Invalid parameter %s"
                            and err.args[0] == 22 else False)

    def test_conf_store_get_by_index_with_chained_index(self):
        """
        Test by getting the chained key(key1.key2.key3) from the loaded config
        at given index
        """
        load_config('test_local1', 'json:///tmp/file1.json')
        result_data = Conf.get('test_local1', 'bridge>lte_type[0]>name')
        self.assertEqual(result_data, '3g')

    def test_conf_store_set_index(self):
        """
        Test by setting the key, value to given index and reading it back.
        """
        load_config('set_local1', 'json:///tmp/file1.json')
        Conf.set('set_local', 'bridge>lte_type[2]>test',
                       {'name': '5g', 'location': 'NY'})
        result_data = Conf.get('set_local', 'bridge>lte_type[2]>test>location')
        self.assertEqual(result_data, 'NY')

    def test_conf_store_set_value_then_dict(self):
        """
        Test by setting the key, string value to given index and
        then try to overwrite it with dict.
        """
        load_config('set_local_2', 'json:///tmp/file1.json')
        # set string value
        Conf.set('set_local_2', 'bridge>lte_type[2]>test', 'sample')
        Conf.set('set_local_2', 'bridge>lte_type[2]>test>nested_test',
                       {'name': '5g', 'location': 'NY'})
        result_data = Conf.get('set_local_2',
                               'bridge>lte_type[2]>test>nested_test>location')
        self.assertEqual(result_data, 'NY')

    def test_conf_store_set_dict_then_string(self):
        """
        Test by setting the key, dict value to given index and
        then try to overwrite it with a string.
        """
        load_config('set_local_3', 'json:///tmp/file1.json')
        Conf.set('set_local_3', 'bridge>lte_type[2]>test>nested_test',
                       {'name': '5g', 'location': 'NY'})
        Conf.set('set_local_3', 'bridge>lte_type[2]>test', 'sample')
        result_data = Conf.get('set_local_3', 'bridge>lte_type[2]>test')
        self.assertEqual(result_data, 'sample')

    def test_conf_store_set_value_with_null_index(self):
        """
        Test by setting the key, value to null index
        """
        load_config('set_local_4', 'json:///tmp/file1.json')
        try:
            Conf.set('set_local_4', 'bridge>lte_type[]>test', 'sample')
        except Exception as err:
            self.assertEqual('Invalid key index for the key lte_type', err.desc)

    def test_conf_store_get_null_index(self):
        """
        Test by getting the null index key.
        """
        load_config('set_local_5', 'json:///tmp/file1.json')
        try:
            Conf.get('set_local_5', 'bridge>lte_type[]')
        except Exception as err:
            self.assertEqual('Invalid key index for the key lte_type', err.desc)

    def test_conf_store_set_with_wrong_key(self):
        """
        Test by setting the value to invalid wrong key.
        """
        load_config('set_local_6', 'json:///tmp/file1.json')
        try:
            Conf.set('set_local_6', 'bridge>lte_type[2]>..',
                           {'name': '5g', 'location': 'NY'})
        except Exception as err:
            self.assertEqual('Invalid key name ', err.desc)

    def test_conf_store_get_with_wrong_key(self):
        """
        Test by getting the invalid wrong key
        """
        load_config('set_local_7', 'json:///tmp/file1.json')
        try:
            Conf.get('set_local_7', 'bridge>lte_type[2]>..>location')
        except Exception as err:
            self.assertEqual('Invalid key name ', err.desc)

    def test_conf_store_set_value_with_empty_in_between(self):
        """
        Test by setting the key, value to given index and
        then try to set 1 more value by skipping the index inbetween.
        """
        load_config('set_local_8', 'json:///tmp/file1.json')
        Conf.set('set_local_8', 'bridge>lte_type[2]', 'sample2')
        Conf.set('set_local_8', 'bridge>lte_type[5]', 'sample5')
        result_data = Conf.get('set_local_8', 'bridge>lte_type')
        # Expected list should match the result_data list output
        expected_result = [
            {'name': '3g'}, {'name': '4g'}, 'sample2', '', '', 'sample5']
        self.assertListEqual(result_data, expected_result)

    def test_conf_store_set_nested_keys(self):
        """
        Test by setting the key, value to given nested key structure
        and retrieve it.
        """
        load_config('set_local_9', 'json:///tmp/file1.json')
        Conf.set('set_local_9', 'bridge>nstd>k1>k2>k3>k4>5>6>7', 'okay')
        result_data = Conf.get('set_local_9', 'bridge>nstd>k1>k2>k3>k4>5>6>7')
        self.assertEqual(result_data, 'okay')

    def test_conf_store_delete_with_index(self):
        """ Test by removing the key, value from the given index. """
        load_config('delete_local_index', 'json:///tmp/file1.json')
        Conf.delete('delete_local_index', 'bridge>lte_type[1]')
        result_data = Conf.get('delete_local_index', 'bridge>lte_type[1]>name')
        self.assertEqual(result_data, None)

    def test_conf_store_set_key_with_hypen(self):
        """
        Test by setting the key with hypen special character in it
        & reading it back.
        """
        load_config('sc_local', 'json:///tmp/file1.json')
        Conf.set('sc_local', 'bridge>proxy-type', 'cloud')
        result_data = Conf.get('sc_local', 'bridge>proxy-type')
        self.assertEqual(result_data, 'cloud')

    def test_conf_store_set_key_with_at(self):
        """
        Test by setting the key with at '@' special character in it
        & reading it back.
        """
        load_config('at_local', 'json:///tmp/file1.json')
        Conf.set('at_local', 'bridge>proxy@type', 'cloud')
        result_data = Conf.get('at_local', 'bridge>proxy@type')
        self.assertEqual(result_data, 'cloud')

    # Properties test
    def test_conf_store_by_load_and_get(self):
        """ Test by loading the give properties config file to in-memory """
        load_config('pro_local', 'properties:///tmp/example.properties')
        result_data = Conf.get_keys('pro_local')
        self.assertTrue('bridge' in result_data)

    def test_conf_store_by_set_and_get(self):
        """ Test by setting the value to given key. """
        Conf.set('pro_local', 'studio_location', 'amritsar')
        result_data = Conf.get('pro_local', 'studio_location')
        self.assertEqual(result_data, 'amritsar')

    def test_conf_store_delte_and_get(self):
        """ Test by removing the key, value from the given index. """
        Conf.delete('pro_local', 'studio_location')
        result_data = Conf.get('pro_local', 'studio_location')
        self.assertEqual(result_data, None)

    def test_conf_store_by_wrong_value(self):
        """ Test by setting the wrong value to given key. """
        Conf.set('pro_local', 'studio_location', '=amritsar')
        Conf.save('pro_local')
        try:
            load_config('pro_local1', 'properties:///tmp/example.properties')
        except Exception as err:
            self.assertEqual('Invalid properties store format %s. %s.', err.args[1])

    # Get_keys API
    def test_conf_key_index_a_True(self):
        """
        Test confStore get_key api with key_index argument as True
        Default key_index will be True
        """
        load_config('getKeys_local', 'json:///tmp/file1.json')
        key_lst = Conf.get_keys("getKeys_local", key_index=True)
        expected_list = ['version', 'branch', 'bridge>name', 'bridge>username',
            'bridge>manufacturer', 'bridge>model', 'bridge>pin', 'bridge>port',
            'bridge>lte_type[0]>name', 'bridge>lte_type[1]>name', 'node_count']
        self.assertListEqual(key_lst, expected_list)

    def test_conf_key_index_b_False(self):
        """ Test confStore get_key api with key_index argument as False """
        key_lst = Conf.get_keys("getKeys_local", key_index=False)
        expected_list = ['version', 'branch', 'bridge>name', 'bridge>username',
            'bridge>manufacturer', 'bridge>model', 'bridge>pin', 'bridge>port',
            'bridge>lte_type>name', 'node_count']
        self.assertListEqual(key_lst, expected_list)

    def test_conf_store_get_machine_id_none(self):
        """ Test get_machine_id None value """
        from cortx.utils.conf_store import ConfStore
        # rename /etc/machine-id
        os.rename("/etc/machine-id", "/etc/machine-id.old")
        cs_inst = ConfStore(delim=Conf._delim)
        mc_id = cs_inst.machine_id
        # restore /etc/machine-id
        os.rename("/etc/machine-id.old", "/etc/machine-id")
        self.assertEqual(mc_id, None)

    def test_conf_store_get_machine_id(self):
        """ Test get_machine_id """
        mc_id = Conf.machine_id
        with open("/etc/machine-id", 'r') as mc_id_file:
            actual_id = mc_id_file.read()
        self.assertEqual(mc_id, actual_id.strip())

    def test_conf_load_fail_reload(self):
        """ Test conf load fail_reload argument """
        Conf.load('reload_index', 'json:///tmp/file1.json')
        expected_lst = Conf.get_keys('reload_index')
        Conf.load('reload_index', 'toml:///tmp/document.toml', fail_reload=False)
        out_lst = Conf.get_keys('reload_index')
        self.assertTrue(True if expected_lst != out_lst else False)

    # search for a key
    def test_conf_store_search_keys(self):
        """Test conf store search key API by passing None value."""
        keys = Conf.search('dict', 'k2', 'k5', None)
        expected = ['k2>k4>k5[0]', 'k2>k4>k5[1]', 'k2>k4>k5[2]']
        self.assertListEqual(expected, keys)

    def test_conf_load_skip_reload(self):
        """ Test conf load skip_reload argument """
        Conf.load('skip_index', 'json:///tmp/file1.json')
        expected_lst = Conf.get_keys('skip_index')
        Conf.load('skip_index', 'toml:///tmp/document.toml', skip_reload=True)
        out_lst = Conf.get_keys('skip_index')
        self.assertTrue(True if expected_lst == out_lst else False)

    def test_conf_load_fail_and_skip(self):
        """ Test conf load fail_reload and skip_reload argument """
        Conf.load('fail_skip_index', 'json:///tmp/file1.json')
        expected_lst = Conf.get_keys('fail_skip_index')
        Conf.load('fail_skip_index', 'toml:///tmp/document.toml', fail_reload=False, skip_reload=True)
        out_lst = Conf.get_keys('fail_skip_index')
        self.assertTrue(True if expected_lst == out_lst else False)

    def test_conf_load_fail_and_skip_non_hap(self):
        """ Test conf load fail_reload True and skip_reload as True argument """
        Conf.load('non_happy_index', 'json:///tmp/file1.json')
        expected_lst = Conf.get_keys('non_happy_index')
        Conf.load('non_happy_index', 'toml:///tmp/document.toml', fail_reload=True, skip_reload=True)
        out_lst = Conf.get_keys('non_happy_index')
        self.assertTrue(True if expected_lst == out_lst else False)

    def test_conf_store_merge_01new_file(self):
        self.assertEqual(Conf.get_keys('dest_index'), [])
        Conf.merge('dest_index', 'src_index')
        Conf.save('dest_index')
        self.assertEqual(Conf.get_keys('dest_index'),
            Conf.get_keys('src_index'))

    def test_conf_store_merge_02no_key(self):
        Conf.set('src_index', 'new_key', 'new_value')
        Conf.save('src_index')
        Conf.merge('dest_index', 'src_index')
        Conf.save('dest_index')
        self.assertEqual(Conf.get('dest_index', 'new_key'), 'new_value')
        self.assertIn('new_key', Conf.get_keys('dest_index'))

    def test_conf_store_merge_03already_key(self):
        Conf.set('dest_index', 'cortx>software>kafka>servers[0]', 'host2.com')
        Conf.save('dest_index')
        Conf.set('src_index', 'cortx>software>kafka>servers[0]', 'host1.com')
        Conf.merge('dest_index', 'src_index')
        Conf.save('dest_index')
        self.assertEqual('host2.com', Conf.get('dest_index',\
            'cortx>software>kafka>servers[0]'))

    def test_conf_store_merge_05update_multiple(self):
        Conf.set('src_index', 'cortx>software>kafka>servers[0]', 'host1.com')
        Conf.set('src_index', 'cortx>software>kafka>servers[1]', 'host2.com')
        Conf.set('src_index', 'cortx>software>kafka>servers[2]', 'host3.com')
        Conf.save('src_index')
        Conf.merge('dest_index', 'src_index')
        Conf.save('dest_index')
        self.assertNotEqual('host1.com', Conf.get('dest_index',
            'cortx>software>kafka>servers[0]'))
        self.assertEqual('host2.com', Conf.get('dest_index',
            'cortx>software>kafka>servers[1]'))
        self.assertEqual('host3.com', Conf.get('dest_index',
            'cortx>software>kafka>servers[2]'))

    def test_conf_store_merge_06_with_keys(self):
        Conf.set('src_index', 'cortx>software>common>test_key1', 'test_value')
        Conf.set('src_index', 'cortx>software>common>test_key2', 'test_value')
        Conf.set('src_index', 'cortx>software>common>message_bus_type', \
            'rabbitmq')
        Conf.save('src_index')
        Conf.merge('dest_index', 'src_index', keys=\
            ['cortx>software>common>test_key1',
             'cortx>software>common>test_key2',
             'cortx>software>common>message_bus_type'])
        Conf.save('dest_index')
        self.assertEqual('test_value', Conf.get('dest_index', \
            'cortx>software>common>test_key1'))
        self.assertEqual('test_value', Conf.get('dest_index', \
            'cortx>software>common>test_key2'))
        self.assertEqual('kafka', Conf.get('dest_index', \
            'cortx>software>common>message_bus_type'))

    def test_conf_store_add_num_keys(self):
        """Test Confstore Add Num keys to config store."""
        Conf.set('src_index', 'test_val[0]', '1')
        Conf.set('src_index', 'test_val[1]', '2')
        Conf.set('src_index', 'test_val[2]', '3')
        Conf.set('src_index', 'test_val[3]', '4')
        Conf.set('src_index', 'test_val[4]', '5')
        Conf.set('src_index', 'test_nested', '2')
        Conf.set('src_index', 'test_nested>2[0]', '1')
        Conf.set('src_index', 'test_nested>2>1[0]', '1')
        Conf.set('src_index', 'test_nested>2>1[1]', '2')
        Conf.set('src_index', 'test_nested>2>1[2]', '3')
        Conf.add_num_keys('src_index')
        self.assertEqual(5, Conf.get('src_index', 'num_test_val'))
        self.assertEqual(3, Conf.get('src_index', 'test_nested>2>num_1'))

    def test_delete(self):
        Conf.load('test_file_1', 'yaml:///tmp/test_file_1.yaml')
        Conf.set('test_file_1', 'a>b>c>d', 'value1')
        Conf.set('test_file_1', 'a1>b>c>d[0]', 11)
        Conf.set('test_file_1', 'a1>b>c>d[1]', 22)

        # Deleting non leaf keys raise KvError
        with self.assertRaises(KvError):
            Conf.delete('test_file_1', 'a1>b>c>d')
        with self.assertRaises(KvError):
            Conf.delete('test_file_1', 'a>b>c')
        with self.assertRaises(KvError):
            Conf.delete('test_file_1', 'a')

        # Delete leaf node
        self.assertEqual(True, Conf.delete('test_file_1', 'a>b>c>d'))
        # Deleting empty intermediate key
        self.assertEqual(True, Conf.delete('test_file_1', 'a>b>c'))
        # Delete non leaf key with force:
        self.assertEqual(True, Conf.delete('test_file_1', 'a', True))
        # Delete indexed key
        self.assertEqual(True,  Conf.delete('test_file_1', 'a1>b>c>d[0]'))

    # DictKVstore tests
    def test_001_conf_dictkvstore_get_all_keys(self):
        """Test conf store get_keys."""
        out = Conf.get_keys('dict', key_index=False)
        expected = ['k1', 'k2>k3', 'k2>k4>k5', 'k2>k4>k6>k7', 'k2>k4>k6>k8']
        self.assertListEqual(expected, out)

    def test_002_conf_dictkvstore_set_get_existing_single_key(self):
        """Test conf store update existing kv."""
        Conf.set('dict', 'k1', 'uv1')
        out = Conf.get('dict', 'k1')
        self.assertEqual('uv1', out)

    def test_003_conf_dictkvstore_set_get_existing_nested_key(self):
        """Test conf store update existing nested kv."""
        Conf.set('dict', 'k2>k4>k6>k8', 'uv8')
        out = Conf.get('dict', 'k2>k4>k6>k8')
        self.assertEqual('uv8', out)
        self.assertEqual('v5', Conf.get('dict', 'k2>k4>k5[1]'))

    def test_004_conf_dictkvstore_set_get_new_single_key(self):
        """Test conf store set kv."""
        Conf.set('dict', 'k9', 'v9')
        out = Conf.get('dict', 'k9')
        self.assertIn('k9', Conf.get_keys('dict'))
        self.assertEqual('v9', out)

    def test_005_conf_dictkvstore_set_get_new_nested_key(self):
        """Test conf store set nested kv."""
        Conf.set('dict', 'k2>k10', 'v10')
        out = Conf.get('dict', 'k2>k10')
        self.assertIn('k2>k10', Conf.get_keys('dict'))
        self.assertEqual('v10', out)

    def test_006_conf_dictkvstore_delete_single_key(self):
        """Test conf store delete kv."""
        Conf.delete('dict', 'k1')
        out = Conf.get('dict', 'k1')
        self.assertNotIn('k1', Conf.get_keys('dict'))
        self.assertIsNone(out)

    def test_007_conf_dictkvstore_delete_nested_key(self):
        """Test conf store delete nested kv."""
        Conf.delete('dict', 'k2>k4>k6>k7')
        out = Conf.get('dict', 'k2>k4>k6>k7')
        self.assertNotIn('k2>k4>k6>k7', Conf.get_keys('dict'))
        self.assertIsNone(out)

    def test_008_conf_dictkvstore_delete_nonexistent_key(self):
        """Test conf store delete non-existent kv."""
        delete_out = Conf.delete('dict', 'k2>k4>k6>k7>k11>k12')
        self.assertFalse(delete_out)

    def test_009_conf_dictkvstore_get_nonexistent_key(self):
        """Test conf store get non-existent kv."""
        out = Conf.get('dict', 'k1>k3>k2')
        self.assertIsNone(out)

    def test_010_conf_dictkvstore_set_value_pass_invalid_key_argument(self):
        """Test conf store pass wrong key argument in Conf.set()."""
        with self.assertRaises(AttributeError):
            Conf.set('dict', {'k13'}, 'v13')

    def test_011_conf_dictkvstore_set_empty_value_to_key(self):
        """Test conf store set empty value to key."""
        Conf.set('dict', 'k1', '')
        out = Conf.get('dict', 'k1')
        self.assertEqual('', out)

    def test_012_conf_dictkvstore_set_value_to_indexed_key(self):
        """Test conf store set value to indexed key."""
        Conf.set('dict', 'k14[6]', 'v14')
        expected = ['', '', '', '', '', '', 'v14']
        out = Conf.get('dict', 'k14')
        self.assertListEqual(expected, out)


    @classmethod
    def tearDownClass(cls):
        delete_files()


if __name__ == '__main__':
    """
    Firstly create the file and load sample json into it.
    Start test
    """
    unittest.main()
