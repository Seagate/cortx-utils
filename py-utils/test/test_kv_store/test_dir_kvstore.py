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

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from cortx.utils.kv_store import KvStoreFactory

class TestDirKvStore(unittest.TestCase):
    """Test store related functionality."""

    def setUp(self):
        self._dir_path = "/tmp/%s" %os.getpid()
        self._kvs = KvStoreFactory.get_instance("dir:%s" %self._dir_path)

    def test_kv_get_set(self):
        data_set = {
            'key1' : 'val1',
            'key2' : 'val2',
            'key3' : 'val3',
        }
        for key, val in data_set.items():
            self._kvs.set([key], [val])

        kv_keys = self._kvs.get_keys()
        for key in data_set.keys():
            self.assertIn(key, kv_keys)
            val = self._kvs.get([key])[0]
            self.assertEqual(val, data_set[key])

    def test_kv_get_set_group(self):
        data_set = {
            'key4' : 'val4',
            'key5' : 'val5',
            'key6' : 'val6',
        }
        self._kvs.set(data_set.keys(), data_set.values())
        kv_keys = self._kvs.get_keys()
        for key in data_set.keys():
            self.assertIn(key, kv_keys)
            val = self._kvs.get([key])[0]
            self.assertEqual(val, data_set[key])

    def test_kv_delete(self):
        data_set = {
            'key7' : 'val7'
        }
        self._kvs.set(data_set.keys(), data_set.values())
        kv_keys = self._kvs.get_keys()
        for key in data_set.keys():
            self.assertIn(key, kv_keys)
        self._kvs.delete(data_set.keys())
        kv_keys = self._kvs.get_keys()
        for key in data_set.keys():
            self.assertNotIn(key, kv_keys)

    def test_kv_set_incorrect(self):
        data_set = {
            'key8' : 'val8',
            'key9' : 'val9'
        }
        try:
            self._kvs.set(data_set.keys(), ['val8'])
            self.assertEqual(0, 1)
        except:
            pass

    def tearDown(self):
        self._deltree(self._dir_path)
        pass

    def _deltree(self, target):
        if not os.path.exists(target):
            return
        for d in os.listdir(target):
            try:
                self._deltree(target + '/' + d)
            except OSError:
                os.remove(target + '/' + d)

        try:
            os.rmdir(target)
        except:
            pass


if __name__ == '__main__':
    unittest.main()