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

from cortx.utils.discovery.resource import Resource
from cortx.utils.discovery.node_health import NodeHealth


class Discovery:
    """
    A common interface of Discovery Module(DM). This will be used for
    resource map, health and manifest generation.
    """

    def __init__(self):
        self.health_gen = NodeHealth()

    def generate_node_health(self, rpath: str = None, store_type: str = "json"):
        """
        This method generates node resource map and health information.

        Health information will be stored in Fs and therefore it fetches
        health information for given rpath later through show interface.
        rpath: Resource path in resource map to fetch its health.
            If rpath is not given, it will fetch whole Cortx Node
            data health and display.
            Examples:
                node[0]>compute[0]>hw>disks
                node[0]>compute
                node[0]>storage[0]
                node[0]>storage[0]>hw>psus
        """
        gen_status = self.get_gen_node_health_status()
        if gen_status == self.health_gen.inprogress:
            return "Failed - Node health generator is busy in processing "\
                "previous request."
        self.health_gen.generate(rpath, store_type)
        return "Success"

    def get_gen_node_health_status(self):
        """
        Returns the below status based on health generator processing state.

        "In-progress" if last health generation request is being processed.
        "Success" if health generation request is completed.
        "Failed (with reason)" if request is failed or denied during processing.
        """
        return self.health_gen.get_processing_status()

    @staticmethod
    def get_node_health(rpath: str = None):
        """
        Fetch and display node health for given rpath.

        rpath: Resource path in resource map to fetch its health.
            If rpath is not given, it will fetch whole Cortx Node
            data health and display.
        """
        val = Resource.get(rpath)
        return val[0] if val else val

    @staticmethod
    def get_resource_map(rpath: str = None, delim: str = ">"):
        """
        Retruns a list of resource types discovered.

        rpath: Resource path in resource map
        Sample Output:
            [
            "compute[0]>hw>platform_sensors>voltage_sensors",
            "compute[0]>hw>platform_sensors",
            "compute[0]>hw>nw_ports",
            "compute[0]>hw",
            "compute[0]>sw>cortx_sw[0]>uid"
            "compute[0]>sw>cortx_sw[1]>uid"
            ]
        """
        if not rpath:
            rpath = Resource.ROOT_NODE
        leaf_node = rpath.split(delim)[-1]
        rmap = {
            leaf_node : Discovery.get_node_health(rpath)
            }
        return Resource.get_keys(rmap)
