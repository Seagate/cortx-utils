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

from cortx.utils.discovery.resource import ResourceFactory

script_path = os.path.realpath(__file__)
data_file = os.path.join(os.path.dirname(script_path), "node_health_info")


class NodeHealth:
    """This generates node health information and updates map"""

    ROOT_NODE = "nodes"
    STATUS = "Ready"
    GEN_MARKER = "/tmp/dm_inprogress"

    def __init__(self):
        """Initialize node health generator"""
        self.inprogress = "In-progress"
        self.success = "Success"
        self.failed = "Failed"

    def generate(self, rpath: str, store_type: str):
        """
        Generates node health information and updates resource map.

        Node health information will be processed and returns completion
        status "Success". If any upcoming request during processing, it
        will return status "In-progress". Retruns "Failed" status with
        reason if current request is failed.
        """
        rpath = rpath if rpath else self.ROOT_NODE
        os.makedirs(NodeHealth.GEN_MARKER, exist_ok=True)
        try:
            resource = ResourceFactory.get_instance(rpath)
            url = "%s://%s.%s" % (store_type, data_file, store_type)
            resource.init(url)
            info = resource.get_health_info(rpath)
            resource.set(rpath, info)
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
