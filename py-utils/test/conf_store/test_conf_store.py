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

def load_config(index, backend_url):
    """Instantiate and Load Config into constore"""
    Conf.load(index, backend_url)
    return Conf


class TestConfStore(unittest.TestCase):
    """Test case will test available API's of ConfStore"""

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

    def test_conf_load_invalid_arguments(self):
        """
        Test by passing invalid argument to confstore load -invalid case
        """
        try:
            Conf.load('invalid_arg', 'json:/tmp/file1.json',
                      test_arg='This is invalid')
        except Exception as err:
            self.assertEqual("load() got an unexpected keyword argument"
                             " 'test_arg'", err.args[0])

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
            {'name': '3g'}, {'name': '4g'}, 'sample2', {}, {}, 'sample5']
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
        expected_list = ['bridge>name', 'bridge>username', 'bridge>manufacturer',
            'bridge>model', 'bridge>pin', 'bridge>port', 'bridge>lte_type[0]>name',
            'bridge>lte_type[1]>name']
        self.assertListEqual(key_lst, expected_list)

    def test_conf_key_index_b_False(self):
        """ Test confStore get_key api with key_index argument as False """
        key_lst = Conf.get_keys("getKeys_local", key_index=False)
        expected_list=['bridge>name', 'bridge>username', 'bridge>manufacturer', 
            'bridge>model', 'bridge>pin', 'bridge>port', 'bridge>lte_type>name']
        self.assertListEqual(key_lst, expected_list)

    def test_conf_store_get_machin_id_none(self):
        """ Test get_machine_id None value """
        from cortx.utils.conf_store import ConfStore
        # rename /etc/machine-id
        os.rename("/etc/machine-id", "/etc/machine-id.old")
        cs_inst = ConfStore(delim=Conf._delim)
        mc_id = cs_inst.machine_id
        # restore /etc/machine-id
        os.rename("/etc/machine-id.old", "/etc/machine-id")
        self.assertEqual(mc_id, None)

    def test_conf_store_get_machin_id(self):
        """ Test get_machine_id """
        mc_id = Conf.machine_id
        with open("/etc/machine-id", 'r') as mc_id_file:
                actual_id = mc_id_file.read()
        self.assertEqual(mc_id, actual_id.strip())

if __name__ == '__main__':
    """
    Firstly create the file and load sample json into it.
    Start test
    """
    setup_and_generate_sample_files()
    unittest.main()
