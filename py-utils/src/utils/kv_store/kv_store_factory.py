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

import os, errno, inspect
from urllib.parse import urlparse
from cortx.utils.kv_store.error import KvStoreError
from cortx.utils.kv_store.kv_store import KvStore
from cortx.utils.kv_store import kv_store_collection


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

        if store_type in KvStoreFactory._stores.keys():
            return KvStoreFactory._stores[store_type]

        storage = inspect.getmembers(kv_store_collection, inspect.isclass)
        for name, cls in storage:
            if hasattr(cls, 'name') and name != "KvStore" and store_type == cls.name:
                KvStoreFactory._stores[store_type] = \
                    cls(store_loc, store_path)
                return KvStoreFactory._stores[store_type]

        raise KvStoreError(errno.EINVAL, "Invalid store type %s", store_type)
