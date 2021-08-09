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

from abc import ABCMeta, abstractmethod


class ResourceMap(metaclass=ABCMeta):
    """Abstract class for all other resource types."""

    name = "resource_map"

    def __init__(self):
        """Initialize resource."""
        pass

    @abstractmethod
    def get_health_info(self, rpath: str):
        """
        Get health information of resource in given rpath.

        :param str rpath: Resource path (Example: hw>disks)
        :return: resource manifest as dictionary or list of dictionary,
            based on input rpath
        """
        pass

    @abstractmethod
    def get_manifest_info(self, rpath: str):
        """
        Get manifest information of resource in given rpath.

        :param str rpath: Resource path (Example: hw>disks)
        :return: resource manifest as dictionary or list of dictionary,
            based on input rpath
        """
        pass
