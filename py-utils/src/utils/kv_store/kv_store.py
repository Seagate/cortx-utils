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

from cortx.utils.kv_store.kv_storage import KvStorageFactory

class KvStore:
    """ Abstraction over all kinds of KV based Storage """

    def __init__(self, store_url):
        self._storage = KvStorageFactory.get_instance(store_url)

    def load(self):
        """ Loads and returns data from KV storage """
        return self._storage.load()

    def save(self, data):
        """ Saves data onto the KV Storage """
        return self._storage.save(data)

    def get(self, key):
        """ Reads value of Key from the KV Storage """
        return self._storage.get(key)

    def set(self, key, value):
        """ Updates the value of Key onto the KV Storage """
        return self._storage.set(key, value)

    def delete(self, key):
        return self._storage.delete(key)


if __name__ == "__main__":
    import sys

    kv_store = KvStore(sys.argv[1])
    data = kv_store.load()
    print(data)
