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
from cortx.utils.conf_store.error import ConfError
from cortx.utils.kv_store.kv_store import KvStore


class ConfCache:
    """ In-memory configuration Data """

    def __init__(self, kv_store: KvStore, delim='>', recurse=True):
        if len(delim) > 1:
            raise ConfError(errno.EINVAL, "invalid delim %s", delim)
        self._delim = delim
        self._dirty = False
        self._kv_store = kv_store
        self._data = None
        self.recurse = recurse
        self.load()

    def get_data(self):
        return self._data

    def get_keys(self, **filters):
        return self._data.get_keys(**filters)

    def load(self):
        """ Loads the configuration from the KV backend """
        if self._dirty:
            raise Exception('%s not synced to disk' % self._kv_store)
        self._data = self._kv_store.load(recurse = self.recurse)

    def dump(self):
        """ Dump the config values onto the corresponding KV backend """
        if self._dirty:
            self._kv_store.dump(self._data)
        self._dirty = False

    def get(self, key: str = None, **filters):
        """ Returns the value corresponding to the key """
        return self._data.get(key, **filters)

    def set(self, key: str, val):
        """ Sets the value into the DB for the given key """
        self._data.set(key, val)
        self._dirty = True

    def add_num_keys(self):
        """
        Add "num_xxx" keys for all the list items in ine KV Store
        """
        self._data.add_num_keys()
        self._dirty = True

    def search(self, parent_key: str, search_key: str, search_val: str) -> list:
        """
        Search for given key and value under a node
        Returns list of keys that matched the creteria (i.e. has given value)
        """
        return self._data.search(parent_key, search_key, search_val)

    def delete(self, key: str):
        """
        Delete a given key from the config.
        Return Value:
        return boolean True for success else False
        """
        result = self._data.delete(key)
        self._dirty = True
        return result
