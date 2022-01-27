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
from cortx.utils.resource_framework import ResourceMap


class HealthMap(ResourceMap):
    """Maintains Health Map at the given KV Store URL"""

    def __init__(self, store_url: str):
        super().__init__(store_url, "health")

    def set_state(self, resource_path: str, state: str):
        self.set(resource_path, "state", state)

    def get_state(self, resource_path) -> str:
        return self.get(resource_path, "state")

if __name__ == "__main__":
    import sys
    hm = HealthMap("yaml:///tmp/health.db")

    hm.set_state("system>node[0]", "degraded")
    hm.set_state("system>node[1]", "degraded")
    hm.set_state("system>node[0]>device[0]", "degraded")
    hm.set_state("system>node[0]>device[1]", "degraded")

    print("state: ", hm.get_state("system>node[0]>device[0]"))
