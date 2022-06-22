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
import unittest

from cortx.utils.conf_store import Conf
from cortx.utils.kv_store.error import KvError

class TestConfStoreIni(unittest.TestCase):
    """Test confstore backend urls mentioned in config file."""

    def _remove_files(self):
        for f in ['/tmp/file1.ini', '/tmp/file2.ini']:
            if os.path.exists(f):
                os.remove(f)

    def setUp(self):
        self._remove_files()
    def tearDown(self):
        self._remove_files()

    def test_conf_store_ini(self):
        # basic set / set
        Conf.load('ini_1', 'ini:///tmp/file1.ini')
        Conf.set('ini_1', 'A>A1', '1')
        Conf.save('ini_1')

        # multi level key not supported by INI
        with self.assertRaises(KvError):
            Conf.set('ini_1', 'A>A1>A2', '1')

        # Check if operations reflected in file
        Conf.load('ini_2', 'ini:///tmp/file1.ini')
        with self.assertRaises(KvError):
            Conf.get('ini_2', 'A>A1>A2')
        self.assertEqual(Conf.get('ini_2', 'A>A1'), '1')
        Conf.delete('ini_2', 'A>A1')
        self.assertEqual(Conf.get('ini_2', 'A>A1'), None)
        self.assertEqual(Conf.get('ini_2', 'FOO>BAR'), None)

        # Confirm delete only reflected in memory
        Conf.load('ini_3', 'ini:///tmp/file1.ini')
        self.assertEqual(Conf.get('ini_2', 'A>A1'), '1')

        # Test copy function
        Conf.load('ini_4', 'ini:///tmp/file2.ini')
        Conf.copy('ini_3', 'ini_4')
        self.assertEqual(Conf.get('ini_4', 'A>A1'), '1')
        with self.assertRaises(KvError):
            Conf.get('ini_4', 'A>A1>A2')
        Conf.save('ini_4')

        # Test key case sensitivity
        Conf.set('ini_3', 'A>A1', '1')
        Conf.set('ini_3', 'a>a1', '2')
        self.assertNotEqual(
            Conf.get('ini_3', 'A>A1'), Conf.get('ini_3', 'A>a1'))


if __name__ == '__main__':
    unittest.main()