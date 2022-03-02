#!/usr/bin/python3.6

# CORTX-Py-Utils: CORTX Python common library.
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

from cortx.utils.kv_store.kv_payload import KvPayload
from cortx.utils.event_framework.event import Attr, Event

class HealthAttr(Attr):
    """Enum class to define constants for health event creation."""

    SOURCE          = 'source'
    CLUSTER_ID      = 'cluster_id'
    SITE_ID         = 'site_id'
    RACK_ID         = 'rack_id'
    STORAGESET_ID   = 'storageset_id'
    NODE_ID         = 'node_id'
    RESOURCE_TYPE   = 'resource_type'
    RESOURCE_ID     = 'resource_id'
    RESOURCE_STATUS = 'resource_status'
    SPECIFIC_INFO   = 'specific_info'

class HealthEvent(Event):
    """Event class for health event messaage schema,
       which initialize and set payload attributes"""

    _health_attrs = [
        HealthAttr.SOURCE, HealthAttr.CLUSTER_ID,
        HealthAttr.SITE_ID, HealthAttr.RACK_ID,
        HealthAttr.STORAGESET_ID, HealthAttr.NODE_ID,
        HealthAttr.RESOURCE_TYPE, HealthAttr.RESOURCE_ID,
        HealthAttr.RESOURCE_STATUS]

    def __init__(self, **kwargs):
        """Initialize payload.
           Param: kwargs = key, value pairs"""
        payload = KvPayload()
        for key in HealthEvent._health_attrs:
            payload.set(str(key), '')
        for key, val in kwargs.items():
            payload.set(key, val)
        payload.set('specific_info', '')
        super().__init__(payload)

    def set(self, key, val):
        super().set_payload_attr(key, val)

    def set_specific_attr(self, key: str, val: str):
        super().set_payload_attr(f'specific_info>{key}', val)

    def set_specific_info(self, spec_info: dict):
        """Set payload attribute of key/value pairs specific to the resource type"""
        specific_info = KvPayload(spec_info)
        for key in specific_info.get_keys():
            super().set_payload_attr(f'specific_info>{key}', specific_info.get(key))
