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
from cortx.utils.conf_store.error import ConfError


class TestConfStoreLockUnlock(unittest.TestCase):
    """Test case will test available API's of ConfStore."""
    @classmethod
    def setUpClass(self):
        self._dir = tempfile.mkdtemp()
        self._url = 'dir://%s' %self._dir
        Conf.load('p1', self._url)
        Conf.load('p2', self._url)
        Conf.load('p3', self._url)

    def test_lock(self):
        """Tests Confstore lock interface"""
        self.assertEqual(True, Conf.lock('p1', owner='p1'))
        Conf.unlock('p1', owner='p1')

    def test_testlock(self):
        """Tests Confstore test_lock interface"""
        Conf.lock('p1', owner='p1')
        self.assertEqual(False, Conf.test_lock('p2', owner='p2'))
        self.assertEqual(True, Conf.test_lock('p1', owner='p1'))
        Conf.unlock('p1', owner='p1')

    def test_unlock(self):
        """Tests Confstore unlock interface"""
        Conf.lock('p1', owner='p1')
        self.assertEqual(True, Conf.unlock('p1', owner='p1'))

    def test_lock_repeat(self):
        """Tests Confstore lock interface repeatedly"""
        self.assertEqual(True, Conf.lock('p1', owner='p1', duration=60))
        self.assertEqual(False, Conf.lock('p2', owner='p2'))
        self.assertEqual(False, Conf.lock('p3', owner='p3'))
        self.assertEqual(True, Conf.lock('p1', owner='p1'))
        Conf.unlock('p1', owner='p1')

    def test_unlock_repeat(self):
        """Tests Confstore unlock interface repeatedly"""
        self.assertEqual(True, Conf.lock('p1', owner='p1', duration=60))
        self.assertEqual(False, Conf.unlock('p2', owner='p2'))
        self.assertEqual(False, Conf.unlock('p3', owner='p3'))
        self.assertEqual(True, Conf.unlock('p1', owner='p1'))
        self.assertEqual(False, Conf.unlock('p1', owner='p1'))

    def test_lock_unlock_negative(self):
        """Tests Wrong index/parameters for lock unlock interface"""
        with self.assertRaises(ConfError):
            Conf.lock('w1', owner='w1')
        with self.assertRaises(ConfError):
            Conf.lock('p1', lock_owner='p1')
        with self.assertRaises(ConfError):
            Conf.unlock('p1', lock_owner='p1', duration=100)

    def test_lock_unlock(self):
        """Tests lock unlock with multiple threads"""
        # lock one thread and try lock from different thread
        Conf.lock('p1', owner='p1', duration=60)
        self.assertEqual(False, Conf.lock('p2', owner='p2', duration=60))
        # try unlock from different threads
        self.assertEqual(False, Conf.unlock('p2', owner='p2'))
        self.assertEqual(False, Conf.unlock('p3', owner='p3'))
        self.assertEqual(True, Conf.unlock('p1', owner='p1'))

    def test_force_unlock(self):
        """Tests force unlock from different thread"""
        Conf.lock('p1', owner='p1', duration=60)
        self.assertEqual(True, Conf.unlock('p2', owner='p2', force=True))

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self._dir)

if __name__ == '__main__':
    # Start test
    unittest.main()
