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
import inspect
from urllib.parse import urlparse

from cortx.utils.kv_store.error import KvStoreError


class KvData:
    """ Base class to represent in memory config data """

    def __init__(self, data):
        self._data = data
        self._keys = []
        self.refresh_keys()

    def get_data(self):
        return self._data

    def get_keys(self):
        return self._keys

    def refresh_keys(self):
        """ Refresh keys. Caller can overrite this """
        self._refresh_keys(self._data)

    def _refresh_keys(self, data, pkey: str = None):
        if type(data) == list:
            for i in range(len(data)):
                self._keys.append("%s[%d]" %(pkey, i))
        elif type(data) == dict:
            for key in data.keys():
                nkey = key if pkey is None else "%s>%s" % (pkey, key)
                if type(data[key]) == str:
                    self._keys.append(nkey)
                else:
                    self._refresh_keys(data[key], nkey)
        else:
            raise KvStoreError(errno.ENOSYS, "Cant handle type %s", type(data))


class DictKvData(KvData):
    """ Dict based in memory representation of conf data """

    def __init__(self, data: dict):
        super(DictKvData, self).__init__(data)

    def _set(self, key: str, val: str, data: dict):
        k = key.split('>', 1)
        if len(k) == 1:
            data[k[0]] = val
            return
        if k[0] not in data.keys():
            data[k[0]] = {}
        self._set(k[1], val, data[k[0]])

    def set(self, key: str, val: str):
        """ Updates the value for the given key in the dictionary """
        return self._set(key, val, self._data)

    def _get(self, key: str, data: dict) -> str:
        k = key.split('>', 1)
        if k[0] not in data.keys(): return None
        return self._get(k[1], data[k[0]]) if len(k) > 1 else data[k[0]]

    def get(self, key: str) -> str:
        """ Obtain value for the given key """
        return self._get(key, self._data)

    def _delete(self, key: str, data: dict):
        k = key.split('>', 1)
        if len(k) == 1:
            if k[0] in data.keys():
                del data[k[0]]
            return
        if k[0] not in data.keys():
            return
        self._delete(k[1], data[k[0]])

    def delete(self, key):
        """ Deletes given set of keys from the dictionary """
        return self._delete(key, self._data)


class KvStore:
    """ Abstraction over all kinds of KV based Storage """

    def __init__(self, store_loc, store_path):
        self._store_loc = store_loc
        self._store_path = store_path

    @property
    def path(self):
        return self._store_path

    @property
    def loc(self):
        return self._store_loc

    def get(self, keys: list) -> list:
        """ Obtains values of keys. Return list of values. """
        data = self.load()
        vals = []
        for key in keys:
            vals.append(data.get(key))
        return vals

    def set(self, keys: list, vals: list):
        """ Updates a given set of keys and values """
        if len(keys) != len(vals):
            raise KvStoreError(errno.EINVAL, f"Mismatched keys & values %s:%s",\
                keys, vals)
        data = self.load()
        for key, val in zip(keys, vals):
            data.set(key, val)
        self.dump(data)

    def delete(self, keys: list):
        """ Deletes given set of keys from the store"""
        data = self.load()
        for key in keys:
            data.delete(key)
        self.dump(data)

    def load(self):
        """ Loads and returns data from KV storage """
        raise KvStoreError(errno.ENOSYS, f"%s:load() not implemented", \
            type(self).__name__)

    def dump(self, data):
        """ Dumps data onto the KV Storage """
        raise KvStoreError(errno.ENOSYS, f"%s:dump() not implemented", \
            type(self).__name__)


class KvStoreFactory:
    """ Factory class for File based KV Store """

    _stores = {}

    def __init__(self):
        """ Initializing KvStoreFactory"""
        pass

    @staticmethod
    def get_instance(store_url: str) -> KvStore:
        """ Obtain instance of KvStore for given file_type """

        url_spec = urlparse(store_url)
        store_type = url_spec.scheme
        store_loc = url_spec.netloc
        store_path = url_spec.path

        if store_url in KvStoreFactory._stores.keys():
            return KvStoreFactory._stores[store_url]

        from cortx.utils.kv_store import kv_store_collection
        storage = inspect.getmembers(kv_store_collection, inspect.isclass)
        for name, cls in storage:
            if hasattr(cls, 'name') and name != "KvStore" and store_type == cls.name:
                KvStoreFactory._stores[store_url] = cls(store_loc, store_path)
                return KvStoreFactory._stores[store_url]

        raise KvStoreError(errno.EINVAL, f"Invalid store type %s", store_type)
