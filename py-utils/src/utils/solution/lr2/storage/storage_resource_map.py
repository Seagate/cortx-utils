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

from cortx.utils.discovery.resource_map import ResourceMap

class StorageResourceMap(ResourceMap):
    """
    StorageResourceMap class provides resource map and related information
    like health, manifest, etc,.
    """

    name = "storage"

    @staticmethod
    def get_health_info(rpath):
        """
        Fetch health information for given resource path.

        rpath: Resource path to fetch its health
               Examples:
                    node>storage[0]
                    node>storage[0]>fw
                    node>storage[0]>fw>logical_volumes
        """
        pass

    @staticmethod
    def get_manifest_info(rpath):
        """
        Fetch manifest information for given resource path.

        rpath: Resource path to fetch its manifest
               Examples:
                    node>storage[0]
                    node>storage[0]>hw
                    node>storage[0]>hw>disks
        """
        pass
