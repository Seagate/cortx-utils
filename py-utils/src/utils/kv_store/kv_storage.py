#!/bin/env python3

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

import os, errno, inspect
from urllib.parse import urlparse
from cortx.utils.kv_store import kv_storage_collections
from cortx.utils.kv_store.error import KvError

class KvStorageFactory:
    """ Factory class for File based KV Storage """

    _storage = {}

    @staticmethod
    def get_instance(store_url):
        """ Obtain instance of KVStorage for given file_type """

        url_spec = urlparse(store_url)
        store_type = url_spec.scheme
        store_path = url_spec.path

        if store_type in KvStorageFactory._storage.keys():
            return KvStorageFactory._storage[store_type]

        storage = inspect.getmembers(kv_storage_collections, \
            inspect.isclass)

        for name, cls in storage:
            if store_type == cls.name:
                KvStorageFactory._storage[store_type] = cls(store_path)
                return KvStorageFactory._storage[store_type]

        raise KvStoreError(errno.EINVAL, "Invalid store type %s", \
            store_type)


class KvStorage:
    """ Base class for File based KV Storage """

    def __init__(self, store_path):
        self._store_path = store_path

    @property
    def store_path(self):
        return self._store_path

    def load(self):
        """ Loads data from file of given format """

        if not os.path.exists(self._store_path):
            return {}
        try:
            return self._load()

        except Exception as e:
            raise KvError(errno.EACCES, 'Failed to read file %s. %s' \
                % (self._store_path, e))

    def dump(self, data):
        """ Store the information back to the file """

        try:
            dir_path = os.path.dirname(self._store_path)

            if len(dir_path) > 0 and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            self._dump(data)

        except OSError as e:
            raise KvError(e.errno, "Unable to save data to %s. %s", \
                (self._store_path, e))

if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    kv_storage = KvStorageFactory.get_instance(url)
    data = kv_storage.load()
    print(data)
