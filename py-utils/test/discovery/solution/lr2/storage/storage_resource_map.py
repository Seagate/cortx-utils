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

from cortx.utils.conf_store import Conf

# Test loads mock data and this module access it using the index
mock_health = "mock-health"
mock_manifest = "mock-manifest"


class StorageResourceMap:

    """Provides health and manifest information of FRUs in storage."""

    name = "storage"

    @staticmethod
    def get_health_info(rpath):
        """
        Fetch health information for given FRU
        rpath: Resource id (Example: node>storage[0]>hw>controller)
        """
        return Conf.get(mock_health, rpath)

    @staticmethod
    def get_manifest_info(rpath):
        """
        Fetch manifest for given FRU
        rpath: Resource id (Example: node>storage[0]>hw>controller)
        """
        return Conf.get(mock_manifest, rpath)
