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

import errno
import inspect

from abc import ABCMeta, abstractmethod
from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.kv_store import KvStoreFactory


class Resource(metaclass=ABCMeta):
    """Update resource map and fetch information based on rpath"""

    ROOT_NODE = "nodes"
    _kv = None

    @abstractmethod
    def get_health_info(self):
        pass

    @staticmethod
    def init(url: str):
        """Read from stored config"""
        if Resource._kv is None:
            Resource._kv = KvStoreFactory.get_instance(url)
            Resource._kv.load()

    @staticmethod
    def set(key: str, value: str):
        """Update key and values"""
        Resource._kv.set([key], [value])

    @staticmethod
    def get(rpath: str):
        """Fetch resource map based on rpath"""
        if not rpath:
            rpath = Resource.ROOT_NODE
        return Resource._kv.get([rpath])

    @staticmethod
    def get_keys(data: dict, delim: str = ">"):
        """Collect all resource map keys"""
        return Resource.traverse_dict(data, delim)

    @staticmethod
    def traverse_dict(dict_data: dict, delim: str):
        """
        Walks through dictionary and returns a list of leaf nodes in full path
        Example,
        input:
            dict_data = {'psus': [{'type': ['AC', 'DC']}, {'health': 'ok'}],
                         'disk': {'id': 'dg01'}}
        output:
            ['psus[0]>type[0]', 'psus[0]>type[1]', 'psus>[1]>>test', 'disks>id']
        """
        stack = []
        final_list = []
        # Meta function to iterate dict values
        def do_walk(datadict):
            if isinstance(datadict, dict):
                for key, value in datadict.items():
                    stack.append(key)
                    if isinstance(value, dict) or isinstance(value, list):
                        do_walk(value)
                    joined_keys = f"{delim}".join(stack).replace(f"{delim}{delim}", "")
                    final_list.append(joined_keys)
                    stack.pop()
            elif isinstance(datadict, list):
                n = 0
                for key in datadict:
                    stack.append(f"{delim}[{str(n)}]")
                    if isinstance(key, dict) or isinstance(key, list):
                        do_walk(key)
                    stack.pop()
                    n = n + 1
        do_walk(dict_data)
        return final_list


class ResourceFactory:
    """Factory class for different resources"""

    _resources = {}

    def __init__(self):
        """Initialize resource factory"""
        pass

    @staticmethod
    def get_instance(rpath: str) -> Resource:
        """Returns instance of ResourceFactory for given rpath"""
        if rpath in ResourceFactory._resources.keys():
            return ResourceFactory._resources[rpath]

        # Parse rpath and find leaf node
        nodes = rpath.strip().split(">")
        leaf_node = nodes[-1] if nodes else nodes

        # Get corresponding class instance
        from cortx.utils.discovery import resource_collection
        resources = inspect.getmembers(resource_collection, inspect.isclass)
        for _, cls in resources:
            if hasattr(cls, 'name') and leaf_node == cls.name:
                ResourceFactory._resources[rpath] = cls
                return ResourceFactory._resources[rpath]

        raise DiscoveryError(errno.EINVAL, "Invalid rpath: '%s'" % rpath)
