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

import os
import sys
import unittest
import tempfile
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from cortx.utils.conf_store import Conf
from cortx.utils.kv_store.error import KvError
from cortx.utils.conf_store.error import ConfError


class TestConfStore(unittest.TestCase):
    """Test case will test available API's of ConfStore."""

    @classmethod
    def setUpClass(self):
        self._dir = tempfile.mktemp()
        self._url = 'dir://%s' %self._dir
        print(self._url)
        Conf.load('i1', self._url)

    def test_set(self):
        """Tests jsonmessage basic operation."""
        Conf.set('i1', 'a>b1', 'v1')
        v = Conf.get('i1', 'a>b1')
        self.assertEqual(Conf.get('i1', 'a>b1'), v)

    def test_get_keys(self):
        Conf.set('i1', 'a>b1', 'v1')
        self.assertEqual(Conf.get_keys('i1'), ['a>b1'])

    def test_delete(self):
        Conf.set('i1', 'a>b1', 'v1')
        Conf.delete('i1', 'a>b1')
        self.assertEqual(Conf.get_keys('i1'), [])
        self.assertEqual(Conf.get('i1', 'a>b1'), None)

    def test_seach(self):
        Conf.set('i1', 'a>b>c>d', 'v2')
        search_keys = Conf.search('i1', 'a', 'd', 'v2')
        self.assertEqual(search_keys, ['a>b>c>d'])

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self._dir)


if __name__ == '__main__':
    # Start test
    unittest.main()
