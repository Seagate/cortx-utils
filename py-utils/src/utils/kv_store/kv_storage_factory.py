#!/bin/python3
import sys
import inspect
import errno

from urllib.parse import urlparse
from src.utils.kv_store.error import KvError
from src.utils.kv_store.file_kv_storage_factory import FileKvStorageFactory
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


class KvStoreFactory:
    _stores = {}

    def __init__(self):
        pass

    @staticmethod
    def get_instance(path_url):
        s_type = urlparse(path_url).scheme
        if s_type in KvStoreFactory._stores.keys():
            return KvStoreFactory._stores[s_type]
        stores = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        for name, cls in stores:
            if name != "KvStore" and name.endswith("Factory"):
                if s_type == cls.name:
                    KvStoreFactory._stores[s_type] = cls(path_url)
                    return KvStoreFactory._stores[s_type]

        raise KvError(errno.EINVAL, "Invalid URL %s", path_url)