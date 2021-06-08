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
import os
import psutil
import re

from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.discovery.resource import Resource, ResourceFactory

script_path = os.path.realpath(__file__)
store_type = "json"
data_file = os.path.join(
    os.path.dirname(script_path), "node_health_info.%s" % store_type)


class NodeHealth:
    """This generates node health information and updates map"""

    STATUS = "Ready"
    GEN_MARKER = "/var/cortx/dm/dm_genhealth_inprogress"
    URL = "%s://%s" % (store_type, data_file)

    def __init__(self):
        """Initialize node health generator"""
        self.ready = "Ready"
        self.inprogress = "In-progress"
        self.success = "Success"
        self.failed = "Failed"

    @staticmethod
    def get_node_details(node):
        """
        Parse node information and returns left string and instance.
        Example
            "storage"    -> ("storage", "*")
            "storage[0]" -> ("storage", "0")
        """
        res = re.search(r"(\w+)\[([\d]+)\]|(\w+)", node)
        inst = res.groups()[1] if res.groups()[1] else "*"
        node = res.groups()[0] if res.groups()[1] else res.groups()[2]
        return node, inst

    def generate(self, rpath: str):
        """Generates node health information and updates resource map"""
        # Deny new request if current scan task is inprogress
        if self.get_processing_status() == self.inprogress:
            raise DiscoveryError(
                errno.EINPROGRESS, "Failed - Node health scan is in-progress.")

        os.makedirs(NodeHealth.GEN_MARKER, exist_ok=True)
        NodeHealth.STATUS = self.success
        info = None
        try:
            # Parse rpath and find left node
            nodes = rpath.strip().split(">")
            leaf_node, _ = self.get_node_details(nodes[-1])

            for num, node in enumerate(nodes, 1):
                node, _ = self.get_node_details(node)
                resource = ResourceFactory.get_instance(node, rpath)

                # Validate next node is its child
                child_found = False
                if node != leaf_node:
                    next_node, _ = self.get_node_details(nodes[num])
                    child_found = resource.has_child(next_node)
                    if resource.childs and not child_found:
                        raise DiscoveryError(
                            errno.EINVAL, "Invalid rpath '%s'" % rpath)

                # Fetch node health information
                if node == leaf_node and len(resource.childs) != 0:
                    info = {}
                    for child in resource.childs:
                        child_inst = ResourceFactory.get_instance(child, rpath)
                        main = resource(child_resource=child_inst)
                        info.update(main.get_health_info(rpath))
                    break
                elif node == leaf_node or len(resource.childs) == 0:
                    main = resource(child_resource=None)
                    info = main.get_health_info(rpath)
                    break

            # Update resource map
            Resource.init(NodeHealth.URL)
            Resource.set(rpath, info)
        except Exception as err:
            NodeHealth.STATUS = self.failed + f" - {err}"
        os.removedirs(NodeHealth.GEN_MARKER)
        return NodeHealth.STATUS

    def get_processing_status(self):
        """
        Returns "in-progress" if any request is being processed.
        Otherwise Node Health scan status is "Ready" or "Success".
        """
        if os.path.exists(NodeHealth.GEN_MARKER):
            NodeHealth.STATUS = self.inprogress
            # Remove marker file if node reboot identified
            last_reboot = int(psutil.boot_time())
            last_modified_time = int(os.stat(NodeHealth.GEN_MARKER).st_mtime)
            if last_reboot > last_modified_time:
                os.removedirs(NodeHealth.GEN_MARKER)
                NodeHealth.STATUS = self.ready
        return NodeHealth.STATUS
