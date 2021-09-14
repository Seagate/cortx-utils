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
# please email opensource@seagate.com or cortx-questions@seagate.com

import re
from cortx.utils.discovery.resource_map import ResourceMap


class ServerResourceMap(ResourceMap):
    """
    ServerResourceMap class provides resource map and related information
    like health, manifest, etc,.
    """

    name = "server"
    # Resources and their common key path.
    resource_indexing_map = {
        "manifest":{
            "sw": {
                "cortx_sw_services": "['uid']",
                "external_sw_services": "['uid']"
            }
        }
    }

    @staticmethod
    def get_manifest_info(rpath):
        """
        Fetch manifest information for given resource path.

        rpath: Resource path to fetch its manifest
               Examples:
                    node>server[0]
        """
        from server.manifest import ServerManifest
        manifest = ServerManifest()
        info = manifest.get_data(rpath)
        return info

    @staticmethod
    def get_health_info(rpath):
        """
        Get health information of resource in given rpath.

        :param str rpath: Resource path (Example: hw>disks)
        :return: resource manifest as dictionary or list of dictionary,
            based on input rpath
        """
        pass

    @staticmethod
    def get_node_info(node):
        """
        Parse node information and returns left string and instance.
        Example
            "storage"    -> ("storage", "*")
            "storage[0]" -> ("storage", "0")

            "server"    -> ("server", "*")
            "server[0]" -> ("server", "0")
        """
        res = re.search(r"(\w+)\[([\d]+)\]|(\w+)", node)
        inst = res.groups()[1] if res.groups()[1] else "*"
        node = res.groups()[0] if res.groups()[1] else res.groups()[2]
        return node, inst
