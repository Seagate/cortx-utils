#!/bin/python3

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


class ConfCache:
    """
    ConfCache implements in-memory configuration management in specified format
    """

    def __init__(self, kv_store_instance):
        self._dirty = False
        self._kvstore = kv_store_instance
        self._data = {}
        self.load()

    def load(self) -> dict:
        if self._dirty:
            raise Exception('%s not synced to disk' % self._kvstore)
        self._data = self._kvstore.load()
        return self._data

    def dump(self):
        """
        Dump the anifest file to desired file or to the source
        """
        self._kvstore.dump(self._data)
        self._dirty = False

    def _get(self, key, data):
        """ Obtain value for the given key """
        k = key.split('.', 1)
        if k[0] not in data.keys(): return None
        return self._get(k[1], data[k[0]]) if len(k) > 1 else data[k[0]]

    def get(self, key) -> dict:
        if self._data is None:
            raise Exception(f"Configuration {self._kvstore} not initialized")
        return self._get(key, self._data)

    def _set(self, key, val, data):
        k = key.split('.', 1)
        if len(k) == 1:
            data[k[0]] = val
            return
        if k[0] not in data.keys() or type(data[k[0]]) != self._kvstore._type:
            data[k[0]] = {}
        self._set(k[1], val, data[k[0]])

    def set(self, key, val) -> None:
        ''' Sets the value into the DB for the given key '''
        self._set(key, val, self._data)
        self._dirty = True
