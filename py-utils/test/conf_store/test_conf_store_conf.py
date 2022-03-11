# !/usr/bin/env python3

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
import sys
from cortx.utils.conf_store import Conf

LOGGER = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
url_config_file = os.path.join(dir_path, 'config.yaml')


def load_index_url():
    """ Load index and url from config file. """
    with open(url_config_file) as fd:
        urls = yaml.safe_load(fd)['conf_url_list']
    for url_index in urls:
        yield [url_index, urls[url_index]]


def load_config(index, backend_url):
    """ Instantiate and Load Config into constore. """
    Conf.load(index, backend_url)


class TestConfStore(unittest.TestCase):
    """ Test confstore backend urls mentioned in config file. """

    _cluster_conf_path = ''
    indexes = []
    _cluster_conf_path = ''

    @classmethod
    def setUpClass(cls, cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """ Setup test class. """
        if TestConfStore._cluster_conf_path:
            cls.cluster_conf_path = TestConfStore._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path

        for index_url in load_index_url():
            index = index_url[0]
            url = index_url[1]
            if index not in TestConfStore.indexes:
                cls.indexes.append(index)

            if 'consul' in index.lower():
                endpoint_key = index_url[1]
                load_config('config', cls.cluster_conf_path)
                endpoint_url = Conf.get('config', 'endpoint_key')
                if endpoint_url is not None:
                    url = endpoint_url.replace('http', 'consul')
                else:
                    LOGGER.error(f'Invalid endpoint key : {endpoint_key}')
                    sys.exit(1)

            load_config(index, url)

    def test_set_and_get(self):
        """ Set and get the value for a key. """
        for index in TestConfStore.indexes:
            Conf.set(index, 'test_key1', 'test_value1')
            get_val = Conf.get(index, 'test_key1')
            self.assertEqual('test_value1', get_val)

    def test_get_keys(self):
        """ set keys and get keys """
        key_list = ['test_k1', 'test_k2', 'test_k3', 'test_k4']
        for index in TestConfStore.indexes:
            for key in key_list:
                Conf.set(index, key, '#!random_value')
            get_key_list = Conf.get_keys(index)
            self.assertTrue(all([True if key in get_key_list else False for key in key_list]))

    def test_get_keys_starts_with(self):
        """set and get keys which starts with a string. """
        key_list = ['swtest_k1', 'swtest_k2', 'swtest_k3', 'swtest_k4']
        for index in TestConfStore.indexes:
            for key in key_list:
                Conf.set(index, key, '#!random_value')
            get_key_list = Conf.get_keys(index, starts_with='swtest')
            self.assertTrue(all([True if key in get_key_list else False for key in key_list]))

    def test_get_wrong_key(self):
        """ Get a wrong key. """
        for index in TestConfStore.indexes:
            val = Conf.get(index, 'Wrong_key')
            self.assertEqual(val, None)

    def test_set_delete_and_get(self):
        """ Get a deleted key. """
        for index in TestConfStore.indexes:
            Conf.set(index, 'K1', 'V1')
            Conf.delete(index, 'K1')
            val = Conf.get(index, 'K1')
            self.assertEqual(val, None)

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        TestConfStore._cluster_conf_path = sys.argv.pop()
    unittest.main()
