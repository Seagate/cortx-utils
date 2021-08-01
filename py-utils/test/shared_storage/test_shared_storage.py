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

import os
import unittest

from cortx.utils.shared_storage import Storage

def get_shared_path(name=None):
    """ Fetch shared path and return. """

    return Storage.get_path(name)

def del_storage_dir(name=None):
    """ Delete mentioned directory. """

    os.rmdir(get_shared_path(name))

class TestSharedStorage(unittest.TestCase):

    """ Unit test class to test shared storage. """

    shared_path = Storage.get_path()

    def test_shared_path_read_access(self):
        """ test if shared storage path exists and is readable. """
        shared_path = Storage.get_path()
        self.assertTrue(os.access(shared_path, os.R_OK))

    def test_shared_path_write_access(self):
        """ test if shared storage path exists and is writable. """
        shared_path = Storage.get_path()
        self.assertTrue(os.access(shared_path, os.W_OK))

    def test_shared_path_with_dir_read_access(self):
        """ test if shared storage path with a dir exists and is readable. """
        shared_path = Storage.get_path('test_path')
        self.assertTrue(os.access(shared_path, os.R_OK))
        del_storage_dir('test_dir')

    def test_shared_path_with_dir_write_access(self):
        """ test if shared storage path with a dir exists and is writable. """
        shared_path = Storage.get_path('test_dir')
        self.assertTrue(os.access(shared_path, os.W_OK))
        del_storage_dir('test_dir')

     def test_shared_path_with_dir_with_exist_ok_False(self):
        """ test if shared storage path with when thealready dir exists. """
        get_shared_path('test_dir')
        get_shared_path('test_dir')
        del_storage_dir('test_dir')


if __name__ == '__main__':
    unittest.main()