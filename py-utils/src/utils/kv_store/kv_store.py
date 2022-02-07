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

from cortx.utils.kv_store.error import KvError
from cortx.utils.kv_store.kv_payload import KvPayload


class KvStore:
    """ Abstraction over all kinds of KV based Storage """

    def __init__(self, store_loc, store_path, delim='>'):
        """
        Args:
        store_loc: store location
        store_path: store path from where to load data
        delim: It is used to split key into hierarchy, e.g. "k1>2" or "k1.k2"
        """
        self._store_loc = store_loc
        self._store_path = store_path
        self._delim = delim

    @property
    def path(self):
        return self._store_path

    @property
    def loc(self):
        return self._store_loc

    @property
    def delim(self):
        return self._delim

    def get_keys(self, key_prefix: str):
        """ returns list of keys starting with given prefix """
        payload = self.load()
        return filter(lambda x: x.startswith(key_prefix), payload.get_keys())

    def search(self, parent_key: str, search_key: str, search_val: str = None):
        """searches for the given key and returs list of matching keys."""
        payload = self.load()
        return payload.search(parent_key, search_key, search_val)

    def add_num_keys(self):
        """writes "num_xxx" keys for all the list items in ine KV Store"""
        payload = self.load()
        payload.add_num_keys()
        self.dump(payload)

    def get_data(self, format_type: str = None) -> str:
        payload = self.load()
        return payload.get_data(format_type)

    def set_data(self, payload: KvPayload):
        """ Updates input payload and writes into backend """
        p_payload = self.load()
        _ = map(lambda x: p_payload.set(x, payload.get[x]), payload.get_keys())
        self.dump(p_payload)

    def get(self, keys: list) -> list:
        """ Obtains values of keys. Return list of values. """
        payload = self.load()
        vals = []
        for key in keys:
            vals.append(payload.get(key))
        return vals

    def set(self, keys: list, vals: list):
        """ Updates a given set of keys and values """
        if len(keys) != len(vals):
            raise KvError(errno.EINVAL, "Mismatched keys & values %s:%s",
                          keys, vals)
        payload = self.load()
        for key, val in zip(keys, vals):
            payload.set(key, val)
        self.dump(payload)

    def delete(self, keys: list):
        """ Deletes given set of keys from the store """
        payload = self.load()
        for key in keys:
            payload.delete(key)
        self.dump(payload)

    def load(self, delim='>'):
        """ Loads and returns data from KV storage """
        raise KvError(errno.ENOSYS, "%s:load() not implemented",
                      type(self).__name__)

    def dump(self, payload, delim='>'):
        """ Dumps data onto the KV Storage """
        raise KvError(errno.ENOSYS, "%s:dump() not implemented",
                      type(self).__name__)


class KvStoreFactory:
    """ Factory class for File based KV Store """

    _stores = {}

    def __init__(self):
        """ Initializing KvStoreFactory """
        pass

    @staticmethod
    def get_instance(store_url: str, delim='>') -> KvStore:
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
            if hasattr(cls, 'name') and store_type == cls.name:
                KvStoreFactory._stores[store_url] = cls(store_loc, store_path,
                                                        delim)
                return KvStoreFactory._stores[store_url]

        raise KvError(errno.EINVAL, "Invalid URL %s", store_url)
