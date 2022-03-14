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

import yaml
import unittest
import logging
import os
from cortx.utils.kv_store import KvStoreFactory
from cortx.utils.conf_store import Conf

LOGGER = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.abspath('.'))
url_config_file = os.path.join(dir_path, 'conf_store', 'config.yaml')


def test_current_file(file_path):
    kv_store = KvStoreFactory.get_instance(file_path)
    data = kv_store.load()
    return [kv_store, data]

# def load_index_url():
#     """ Load index and url from config file. """
#     with open(url_config_file) as fd:
#         urls = yaml.safe_load(fd)['conf_url_list']
#     for url_index in urls.keys():
#         if 'consul' in url_index:
#             yield urls[url_index]


# def load_consul_endpoint(endpoint_key, cluster_conf_url):
#     Conf.load('config', cluster_conf_url)
#     endpoint_url = Conf.get('config', endpoint_key)
#     return endpoint_url


class TestStore(unittest.TestCase):

    _cluster_conf_path = ''
    _loaded_consul = ''

    @classmethod
    def setUpClass(cls, cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """ Setup test class. """
        if TestStore._cluster_conf_path:
            cls.cluster_conf_path = TestStore._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path

        with open(url_config_file) as fd:
            urls = yaml.safe_load(fd)['conf_url_list']
            endpoint_key = urls['consul_endpoints']

        Conf.load('config', cls.cluster_conf_path)
        endpoint_url = Conf.get('config', endpoint_key)

        # for endpoint_key in load_index_url():
        #     endpoint_url = load_consul_endpoint(endpoint_key, cls.cluster_conf_path)
        if endpoint_url is not None and 'http' in endpoint_url:
            url = endpoint_url.replace('http', 'consul')
        else:
            LOGGER.error(f'\nInvalid consul endpoint key : {endpoint_key}\n')

        TestStore._loaded_consul = test_current_file(url)

    def test_consul_a_set_get_kv(self):
        """ Test consul kv set and get a KV. """
        TestStore._loaded_consul[0].set(['consul_cluster_uuid'], ['#410'])
        out = TestStore._loaded_consul[0].get(['consul_cluster_uuid'])
        self.assertEqual('#410', out[0])

    def test_consul_b_query_unknown_key(self):
        """ Test consul kv query for an absent key. """
        out = TestStore._loaded_consul[0].get(['Wrong_key'])
        self.assertIsNone(out[0])

    def test_consul_store_c_set_nested_key(self):
        """ Test consul kv set a nested key. """
        TestStore._loaded_consul[0].set(['consul_cluster>uuid'], ['#411'])
        out = TestStore._loaded_consul[0].get(['consul_cluster>uuid'])
        self.assertEqual('#411', out[0])

    def test_consul_store_d_set_multiple_kv(self):
        """ Test consul kv by setting nested key structure """
        TestStore._loaded_consul[0].set(['cloud>cloud_type', 'kafka>message_type'],
            ['Azure', 'receive'])
        out1 = TestStore._loaded_consul[0].get(['kafka>message_type'])
        out2 = TestStore._loaded_consul[0].get(['cloud>cloud_type'])
        self.assertEqual('receive', out1[0])
        self.assertEqual('Azure', out2[0])

    def test_consul_store_e_delete_kv(self):
        """ Test consul kv by removing given key using delete api """
        TestStore._loaded_consul[0].delete(['cloud>cloud_type'])
        out = TestStore._loaded_consul[0].get(['cloud>cloud_type'])
        self.assertEqual([None], out)

    def test_consul_store_f_set_value_null(self):
        """Test consul kv by setting empty string as value."""
        TestStore._loaded_consul[0].set(['test'],[''])
        out = TestStore._loaded_consul[0].get(['test'])
        TestStore._loaded_consul[0].delete(['test'])
        self.assertEqual([''], out)

    def test_consul_store_g_set_search(self):
        """Test consul search."""
        TestStore._loaded_consul[0].set(['test>child_key>leaf_key'],['value'])
        out = TestStore._loaded_consul[0].search('test', 'leaf_key', 'value')
        TestStore._loaded_consul[0].delete(['test>child_key>leaf_key'])
        self.assertEqual(['test>child_key>leaf_key'], out)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        TestStore._cluster_conf_path = sys.argv.pop()
    unittest.main()
