#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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
from cortx.utils.kv_store import KvStoreFactory

def test_current_file(file_path):
    kv_store = KvStoreFactory.get_instance(file_path)
    data = kv_store.load()
    return [kv_store, data]

class TestStore(unittest.TestCase):

    loaded_consul = test_current_file('consul:///')

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


if __name__ == '__main__':
    unittest.main()
