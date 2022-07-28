#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
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

from cortx.utils.conf_store import Conf


class TestConfStoreConsul(unittest.TestCase):
    """Test Conf Store with Consul as backend."""

    _consul_url = "consul://cortx-consul-server:8500"
    _store_path = _consul_url + "/test_gconf"
    _consul_idx = "_consul_idx"

    def setUp(self):
        self._load_config()

    def _load_config(self):
        """Load consul config."""
        Conf.load(TestConfStoreConsul._consul_idx,  TestConfStoreConsul._store_path)

    def test_add_num_keys(self):
        """Test Confstore Add Num keys to KV store."""
        _index = TestConfStoreConsul._consul_idx
        _val = '_'
        _keys = [
            'no_num', 'test_val[0]', 'test_val[1]', 'test_nested>2[0]>1>3[0]',
            'test_nested>2[0]>1>3[1]', 'test_nested>2[0]>1>3[2]',
        ]
        for _key in _keys:
            Conf.set(_index, _key, _val)
        Conf.add_num_keys(_index)
        self.assertIsNone(Conf.get(_index, 'num_no_num'))
        self.assertEqual(2, int(Conf.get(_index, 'num_test_val')))
        self.assertEqual(1, int(Conf.get(_index, 'test_nested>num_2')))
        self.assertEqual(3, int(Conf.get(_index, 'test_nested>2[0]>1>num_3')))
        for _key in _keys:
            Conf.delete(_index, _key, _val)
        Conf.delete(_index, 'num_test_val')
        Conf.delete(_index, 'test_nested>num_2')
        Conf.delete(_index, 'test_nested>2[0]>1>num_3')

    def tearDown(self):
        """Clean Up."""
        pass


if __name__ == '__main__':
    unittest.main()
