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
from const import HEALTH_EVENT_ATTRIBUTES, HEALTH_EVENT_HEADER, \
    HEALTH_EVENT_PAYLOAD
import time
import uuid

VERSION = "1.0"


class Event:
    
    """
    Class for health status event message schema,
    where producer can import this class object and add it
    in there existing schema.
    """

    def __init__(self):
        """
        Initialize default value for header and payload component.
        """
        self.event = {}
        header = {}
        header[HEALTH_EVENT_ATTRIBUTES.VERSION] = VERSION
        header[HEALTH_EVENT_ATTRIBUTES.TIMESTAMP] = str(int(time.time()))
        header[HEALTH_EVENT_ATTRIBUTES.EVENT_ID] =  \
            header[HEALTH_EVENT_ATTRIBUTES.TIMESTAMP] + \
            str(uuid.uuid4().hex)
        self.event[HEALTH_EVENT_HEADER] = header

        payload = {}
        payload[HEALTH_EVENT_ATTRIBUTES.SOURCE] = None
        payload[HEALTH_EVENT_ATTRIBUTES.CLUSTER_ID] = None
        payload[HEALTH_EVENT_ATTRIBUTES.SITE_ID] = None
        payload[HEALTH_EVENT_ATTRIBUTES.RACK_ID] = None
        payload[HEALTH_EVENT_ATTRIBUTES.STORAGESET_ID] = None
        payload[HEALTH_EVENT_ATTRIBUTES.NODE_ID] = None
        payload[HEALTH_EVENT_ATTRIBUTES.RESOURCE_TYPE] = None
        payload[HEALTH_EVENT_ATTRIBUTES.RESOURCE_ID] = None
        payload[HEALTH_EVENT_ATTRIBUTES.RESOURCE_STATUS] = None
        payload[HEALTH_EVENT_ATTRIBUTES.SPECIFIC_INFO] = {}
        self.event[HEALTH_EVENT_PAYLOAD] = payload

    def set_payload(self, _input):
        """
        Update payload values.
        params: payload data of attributes with value type : dict
        _input = {"source" : "hare", "node_id" : "2"}
        """
        for key in _input.keys():
            if key in list(self.event[HEALTH_EVENT_PAYLOAD].keys()):
                self.event[HEALTH_EVENT_PAYLOAD][key] = _input[key]
            else:
                specific_info = HEALTH_EVENT_ATTRIBUTES.SPECIFIC_INFO
                self.event[HEALTH_EVENT_PAYLOAD][specific_info][key] \
                    = _input[key]
