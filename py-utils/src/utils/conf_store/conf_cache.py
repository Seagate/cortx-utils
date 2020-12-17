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

import errno
from cortx.utils.conf_store.error import ConfStoreError
from cortx.utils.kv_store.kv_store import KvStore


class ConfCache:
    """ In-memory configuration Data """

    def __init__(self, kv_store: KvStore):
        self._dirty = False
        self._kv_store = kv_store
        self._data = {}
        self.load()

    def get_data(self):
        return self._data

    def get_keys(self):
        return self._keys

    def load(self):
        """ Loads the configuration from the KV backend """
        if self._dirty:
            raise Exception('%s not synced to disk' % self._kv_store)
        self._data = self._kv_store.load()

        self._keys = []
        self._refresh_keys(self._data)

    def dump(self):
        """ Dump the config values onto the corresponding KV backend """
        self._kv_store.dump(self._data)
        self._dirty = False

    def _refresh_keys(self, data, pkey: str = None):
        if type(data) == list:
            for i in range(len(data)):
                self._keys.append("%s[%d]" %(pkey, i))
        elif type(data) == dict: 
            for key in data.keys():
                nkey = key if pkey is None else "%s.%s" %(pkey, key)
                if type(data[key]) == str or type(data[key]) == int: self._keys.append(nkey)
                else: self._refresh_keys(data[key], nkey)
        else:
            raise ConfStoreError(errno.ENOSYS, "Cant handle type %s", type(data))
                
    def __iter__(self):
        self._iter = 0
        return self

    def __next__(self):
        if self._iter >= len(self._keys):
            raise StopIteration
        key = self._keys[self._iter]
        self._iter += 1
        return key

    def _get(self, data: dict, key: str):
        """ Obtain value for the given key """
        k = key.split('.', 1)
        if k[0] not in data.keys(): return None
        return self._get(data[k[0]], k[1]) if len(k) > 1 else data[k[0]]

    def get(self, key: str):
        """ Returns the value corresponding to the key """
        return self._get(self._data, key)

    def _set(self, data: dict, key: str, val):
        k = key.split('.', 1)
        if len(k) == 1:
            data[k[0]] = val
            return
        if k[0] not in data.keys(): data[k[0]] = {}
        self._set(data[k[0]], k[1], val)

    def set(self, key: str, val):
        """ Sets the value into the DB for the given key """
        self._set(self._data, key, val)
        self._dirty = True
        if key not in self._keys:
            self._keys.append(key)

    def _delete(self, data: dict, key: str):
        k = key.split('.', 1)
        if k[0] not in data.keys(): return 
        if len(k) > 1: return self._delete(data[k[0]], k[1])
        del data[k[0]]
        if key in self._keys:
            self._keys.remove(key)

    def delete(self, key: str):
        """ Delets a given key from the config """
        self._delete(self._data, key)
