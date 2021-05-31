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
import os

from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.discovery.resource_map import ResourceMap


class NodeHealthGenerator:
    """This generates node health information and updates map"""

    ROOT_NODE = "nodes"
    STATUS = "Ready"
    GEN_MARKER = "/tmp/dm_inprogress"

    def __init__(self):
        """Initialize node health generator"""
        self.inprogress = "In-progress"
        self.success = "Success"
        self.failed = "Failed"

    def run(self, rpath: str = None):
        """
        Generates node health information and updates resource map.

        Node health information will be processed and returns completion
        status "Success". If any upcoming request during processing, it
        will return status "In-progress". Retruns "Failed" status with
        reason if current request is failed.
        """
        rpath = rpath if rpath else self.ROOT_NODE
        os.makedirs(NodeHealthGenerator.GEN_MARKER, exist_ok=True)
        try:
            resource = ResourceFactory.get_instance(rpath)
            info = resource.generate_health_info()
            ResourceMap.load()
            ResourceMap.set(rpath, info)
            NodeHealthGenerator.STATUS = self.success
        except Exception as err:
            NodeHealthGenerator.STATUS = self.failed + str(err)
        os.removedirs(NodeHealthGenerator.GEN_MARKER)
        return NodeHealthGenerator.STATUS

    def get_processing_status(self):
        """
        Returns "in-progress" is any request is under processing.
        Otherwise generator processing status is "Ready" or "Success".
        """
        if os.path.exists(NodeHealthGenerator.GEN_MARKER):
            NodeHealthGenerator.STATUS = self.inprogress
        return NodeHealthGenerator.STATUS


class ResourceFactory:
    """Factory class for different resources"""

    _resources = {}

    def __init__(self):
        """Initialize resource factory"""
        pass

    @staticmethod
    def get_instance(rpath):
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
                ResourceFactory._resources[rpath] = cls(leaf_node, rpath)
                return ResourceFactory._resources[rpath]

        raise DiscoveryError(errno.EINVAL, "Invalid rpath '%s'", rpath)
