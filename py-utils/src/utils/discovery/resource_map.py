#!/bin/python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import os

from cortx.utils.conf_store import ConfStore


script_path = os.path.realpath(__file__)
data_file = os.path.join(os.path.dirname(script_path), "node_health_info.json")


class ResourceMap:
    """Update resource map and fetch information based on rpath"""

    ROOT_NODE = "nodes"
    _conf = None
    _delim = '>'
    index = "healthmap"
    url = "json://%s" % data_file

    @staticmethod
    def load():
        """Read from stored config"""
        if ResourceMap._conf is None:
            ResourceMap._conf = ConfStore(delim=ResourceMap._delim)
            ResourceMap._conf.load(ResourceMap.index, ResourceMap.url)

    @staticmethod
    def set(key: str, value: str):
        """Update key and values"""
        ResourceMap.load()
        ResourceMap._conf.set(ResourceMap.index, key, value)
        ResourceMap._conf.save(ResourceMap.index)

    @staticmethod
    def get(rpath: str):
        """Fetch resource map based on rpath"""
        if not rpath:
            rpath = ResourceMap.ROOT_NODE
        ResourceMap.load()
        return ResourceMap._conf.get(ResourceMap.index, rpath)

    @staticmethod
    def get_keys(rpath: str = None):
        """Collect all resource map keys"""
        return ResourceMap._conf.get_keys(ResourceMap.index)
