#!/bin/python3
import os, errno, sys
from src.utils.kv_store import KvStore

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

class FileKvStorage(KvStore):
    '''
    FileKvStorage base implementation Provides generic interfaces for derived FileStorage classes
    like Json, Yaml and Ini
    '''
    _type = dict

    def __init__(self, file_path):
        self._file_path = self.get_url(file_path)

    def __str__(self):
        return str(self._file_path)

    def load(self):
        ''' Loads data from file of given format '''
        if not os.path.exists(self._file_path):
            return {}
        try:
            return self._load()
        except Exception as e:
            raise Exception('Unable to read file %s. %s' % (self._file_path, e))

    def dump(self, data):
        ''' Dump the anifest file to desired file or to the source '''
        dir_path = os.path.dirname(self._file_path)
        if len(dir_path) > 0 and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self._dump(data)

    def get_url(self, file_path):
        try:
            if 'file://' in file_path:
                # Consider that supplied url as file type
                out = file_path.split('file://')
                return out[-1]
        except Exception as e:
            raise Exception(f"Invalid path given")