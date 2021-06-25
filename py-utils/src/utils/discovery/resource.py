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
import importlib
import inspect
import os
import sys

from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.kv_store import KvStoreFactory


class Resource:
    """Abstraction over all resource type"""

    ROOT_NODE = "node"
    _kv = None

    def __init__(self, name, child_resource=None):
        """Initialize resource"""
        self._name = name
        self._child_resource = child_resource
        self.health_provider_map = {
            "storage": "storage",
            "compute": "server"
            }

    @property
    def name(self):
        return self._name

    @property
    def child_resource(self):
        return self._child_resource

    @staticmethod
    def init(url: str):
        """Read from stored config"""
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
    def get_health_provider_module(path, product_id):
        """Look for solution specific __init__ module in health provider path"""
        module = None
        try:
            if path.startswith("/"):
                if path not in sys.path:
                    sys.path.append(path)
                module_path = os.path.join(path, product_id)
                if module_path not in sys.path:
                    sys.path.append(module_path)
                module = __import__("%s.__init__" % product_id)
            else:
                m_path = os.path.join(path.strip(), product_id).replace("/", ".")
                module = importlib.import_module(m_path)
        except ModuleNotFoundError:
            raise DiscoveryError(
                errno.ENOENT,
                "Failed to import health provider module from configured path - %s" % path)
        return module

    def get_health_info(self, rpath):
        """Initialize health provider module and fetch health information"""
        from cortx.utils.discovery.node_health import common_config
        monitor_path = common_config.get(
            ["discovery>solution_platform_monitor"])[0]
        product_id = common_config.get(["product_id"])[0].lower()
        module = self.get_health_provider_module(monitor_path, product_id)
        members = inspect.getmembers(module, inspect.isclass)
        for _, cls in members:
            if hasattr(cls, 'name') and self.health_provider_map[self.name] == cls.name:
                return cls().get_health_info(rpath)
        raise DiscoveryError(
            errno.EINVAL,
            "%s health provider not found in configured path %s" % (
                self.health_provider_map[self.name].title(), monitor_path))


class ResourceFactory:
    """Factory class for different resources"""

    _resources = {}

    def __init__(self):
        """Initialize resource factory"""
        pass

    @staticmethod
    def get_instance(node: str, rpath: str) -> Resource:
        """
        Returns instance of ResourceFactory for given rpath.

        Created cls instance will be reused if generate node
        health is called for same rpath again.
        """
        # Get corresponding class instance
        from cortx.utils.discovery import resource_collection
        resources = inspect.getmembers(resource_collection, inspect.isclass)
        for _, cls in resources:
            if hasattr(cls, 'name') and node == cls.name:
                ResourceFactory._resources[rpath] = cls
                return ResourceFactory._resources[rpath]

        raise DiscoveryError(errno.EINVAL, "Invalid rpath: '%s'" % rpath)
