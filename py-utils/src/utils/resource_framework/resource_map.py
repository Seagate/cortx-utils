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


from cortx.utils.kv_store import KvStoreFactory


class ResourceMap:
    """Maintains Resource Map at the given KV Store URL"""

    def __init__(self, store_url: str, domain: str = "resource"):
        self._domain = domain
        self.store_url = store_url
        self._store = KvStoreFactory.get_instance(store_url)

    def set(self, resource_path: str, attr: str, val: str):
        resource_key = f"{self._domain}>{resource_path}>{attr}"
        self._store.set([resource_key], [val])

    def get(self, resource_path, attr) -> str:
        resource_key = f"{self._domain}>{resource_path}>{attr}"
        return self._store.get([resource_key])[0]
