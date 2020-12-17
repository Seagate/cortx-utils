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

import asyncio
import json
import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from cortx.utils.schema.payload import Json
from cortx.utils.conf_store import Conf

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_conf_sample_json.json')
sample_config = Json(file_path).load()


def setup_and_generate_sample_files():
    """ This function will generate all required types of file """
    with open(r'/tmp/config.json', 'w+') as file:
        json.dump(sample_config, file, indent=2)


conf = Conf()


def load_config(index, backend_url):
    """
    Instantiate and Load Config into constore
    """
    # conf_backend = KvStoreFactory.get_instance(backend_url)
    Conf.load(index, backend_url)
    return Conf


class TestConfStore(unittest.TestCase):
    """
    Test case will test available API's of ConfStore
    """

    def test_conf_store_load_and_get(self):
        """
        Test by loading the give config file to in-memory
        """
        load_config('sspl_local', 'json:///tmp/file1.json')
        result_data = Conf.get('sspl_local', 'bridge')
        self.assertTrue(True if 'name' in result_data else False)

    def test_conf_store_get_by_index_with_single_key(self):
        """
        Test by getting the key from the loaded config
        """
        load_config('msg_local', 'json:///tmp/file1.json')
        result_data = Conf.get('msg_local', 'bridge')
        self.assertTrue(True if 'name' in result_data else False)

    def test_conf_store_get_by_index_with_chained_key(self):
        """
        Test by getting the chained key(key1.key2.key3) from the loaded config
        """
        load_config('test_local', 'json:///tmp/file1.json')
        result_data = Conf.get('test_local', 'bridge.name')
        self.assertEqual(result_data, 'Homebridge')

    def test_conf_store_get_wrong_key(self):
        """
        Test by trying to get the wrong key from the loaded config
        """
        load_config('new_local', 'json:///tmp/file1.json')
        result_data = Conf.get('test_local', 'bridge.no_name_field')
        self.assertEqual(result_data, None)

    def test_conf_store_set(self):
        """
        Test by setting the key, value to given index and reading it back.
        """
        load_config('set_local', 'json:///tmp/file1.json')
        Conf.set('set_local', 'bridge.proxy', 'no')
        result_data = Conf.get('set_local', 'bridge.proxy')
        self.assertEqual(result_data, 'no')

    def test_conf_store_get_keys(self):
        load_config('get_keys_local', 'json:///tmp/file1.json')
        result_data = Conf.get_keys('get_keys_local')
        self.assertTrue(True if len(result_data) > 1 else False)

    def test_conf_store_delete(self):
        load_config('delete_local', 'json:///tmp/file1.json')
        Conf.delete('delete_local', 'bridge.proxy')
        result_data = Conf.get('delete_local', 'bridge.proxy')
        self.assertEqual(result_data, None)


async def run_test():
    """
    Firstly create the file and load sample json into it.
    """
    # setup_and_generate_sample_files()
    await asyncio.sleep(2)
    unittest.main()

if __name__ == '__main__':
    """
    Start test
    """
    asyncio.run(run_test())
