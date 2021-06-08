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

from cortx.utils.discovery.node_health import NodeHealth


class Discovery:
    """Common interfaces of Discovery Module(DM)"""

    def __init__(self):
        self.root_node = "nodes"
        self.health_gen = NodeHealth()

    def generate_node_health(self, rpath: str = None):
        """
        This method generates node resource map and health information.
        rpath: Resource path in resource map to fetch its health.
            If rpath is not given, it will fetch whole Cortx Node
            data health and display.
            Examples:
                node[0]>compute[0]>hw>disks
                node[0]>compute[0]
                node[0]>storage[0]
                node[0]>storage[0]>hw>psus
        """
        rpath = rpath if rpath else self.root_node
        gen_status = self.health_gen.generate(rpath)
        return gen_status

    def get_gen_node_health_status(self):
        """
        Returns the below status based on health generator processing state.

        "In-progress" if last health generation request is being processed.
        "Success" if health generation request is completed.
        "Failed (with reason)" if request is failed or denied during processing.
        """
        return self.health_gen.get_processing_status()

    @staticmethod
    def get_node_health():
        """
        Return resource health map backend URL.
        URL format: "json://<file_path>/<file_name>"
        """
        return NodeHealth.URL
