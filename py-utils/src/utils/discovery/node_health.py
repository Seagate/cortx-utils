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
import re

from cortx.utils.discovery.resource import Resource, ResourceFactory

script_path = os.path.realpath(__file__)
store_type = "json"
data_file = os.path.join(
    os.path.dirname(script_path), "node_health_info.%s" % store_type)


class NodeHealth:
    """This generates node health information and updates map"""

    STATUS = "Ready"
    GEN_MARKER = "/var/cortx/dm/dm_inprogress"
    URL = "%s://%s" % (store_type, data_file)

    def __init__(self):
        """Initialize node health generator"""
        self.inprogress = "In-progress"
        self.success = "Success"
        self.failed = "Failed"

    @staticmethod
    def get_node_details(node):
        res = re.search(r"(\w+)\[([\d]+)\]|(\w+)", node)
        inst = res.groups()[1] if res.groups()[1] else "*"
        node = res.groups()[0] if res.groups()[1] else res.groups()[2]
        return node, inst

    def generate(self, rpath: str):
        """Generates node health information and updates resource map"""
        os.makedirs(NodeHealth.GEN_MARKER, exist_ok=True)
        info = None
        try:
            # Parse rpath and find left node
            nodes = rpath.strip().split(">")
            leaf_node, inst = self.get_node_details(nodes[-1])
            for num, node in enumerate(nodes, 1):
                node, inst = self.get_node_details(node)
                resource = ResourceFactory.get_instance(node, rpath)
                # Validate next node is its child
                child_found = False
                if node != leaf_node:
                    child_found = True if resource.has_child(nodes[num]) else False
                if not child_found or node == leaf_node:
                    main = resource(child_resource=None, inst=inst)
                    info = main.get_health_info(
                        rid=">".join(nodes[num:]))
                    break
            Resource.init(NodeHealth.URL)
            Resource.set(rpath, info)
            NodeHealth.STATUS = self.success
        except Exception as err:
            NodeHealth.STATUS = self.failed + f" - {err}"
        os.removedirs(NodeHealth.GEN_MARKER)
        return NodeHealth.STATUS

    def get_processing_status(self):
        """
        Returns "in-progress" is any request is under processing.
        Otherwise generator processing status is "Ready" or "Success".
        """
        if os.path.exists(NodeHealth.GEN_MARKER):
            NodeHealth.STATUS = self.inprogress
        return NodeHealth.STATUS
