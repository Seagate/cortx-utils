#!/usr/bin/python3.6

# CORTX-Py-Utils: CORTX Python common library.
<<<<<<< HEAD
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
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


class HEALTH_EVENT_SOURCES(Enum):
    HA = "ha"
    HARE = "hare"
    MONITOR = "monitor"


class HEALTH_EVENT_ATTRIBUTES:
    VERSION = "version"
    TIMESTAMP = "timestamp"
    EVENT_ID = "event_id"
    SOURCE = "source"
    CLUSTER_ID = "cluster_id"
    SITE_ID = "site_id"
    RACK_ID = "rack_id"
    STORAGESET_ID = "storageset_id"
    NODE_ID = "node_id"
    RESOURCE_TYPE = "resource_type"
    RESOURCE_ID = "resource_id"
    RESOURCE_STATUS = "resource_status"
    SPECIFIC_INFO = "specific_info"


HEALTH_EVENT_HEADER = "header"
HEALTH_EVENT_PAYLOAD = "payload"
