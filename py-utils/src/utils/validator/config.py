#!/bin/python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

from enum import Enum

class Bmc_V_Types(Enum):
    """ Enumeration for BMC validation types """
    ACCESSIBLE = "accessible"
    STONITH = "stonith"

class Consul_V_Types(Enum):
    """ Enumeration for Consul validation types """
    SERVICE = "service"

class Elasticsearch_V_Types(Enum):
    """ Enumeration for Elastic Search validation types """
    SERVICE = "service"

class Network_V_Types(Enum):
    """ Enumeration for Network validation types """
    CONNECTIVITY = "connectivity"
    PASSWORDLESS = "passwordless"
    DRIVERS = "drivers"
    HCA = "hca"

class Salt_V_Types(Enum):
    """ Enumeration for Salt validation types """
    MINIONS = "minions"

class Storage_V_Types(Enum):
    """ Enumeration for Storage validation types """
    HBA = "hba"
    LUNS = "luns"
    LVMS = "lvms"

# validations parameters
LUNS_CHECKS = ['accessible', 'mapped', 'size']
HBA_PROVIDER = ["lsi"] # More providers can be added in future, if required.
HCA_PROVIDERS = ["mellanox"] # More providers can be added to the list in future, if required.
