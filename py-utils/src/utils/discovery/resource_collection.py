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


class Disks:
    """Represents Disk instances"""

    name = "disks"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Disks.info


class Psus:
    """Represents PSU instances"""

    name = "psus"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Psus.info


class Hardware(Disks, Psus):
    """Represents Hardware type instances"""

    name = "hw"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Hardware.info


class Software:
    """Represents Software type instances"""

    name = "sw"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Software.info


class Compute(Hardware, Software):
    """Represents Compute instances"""

    name = "compute"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Compute.info


class Storage(Hardware, Software):
    """Represents Storage instances"""

    name = "storage"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Storage.info


class Nodes(Compute, Storage):
    """Represents Node instances"""

    name = "nodes"
    info = {}

    def __init__(self, lnode, rpath):
        pass

    @staticmethod
    def generate_health_info():
        return Nodes.info
