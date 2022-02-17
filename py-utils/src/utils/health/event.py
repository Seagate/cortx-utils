#!/usr/bin/python3.6

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
from const import HEALTH_EVENT_ATTRIBUTES
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
        self.header = {}
        self.header[HEALTH_EVENT_ATTRIBUTES.VERSION] = VERSION
        self.header[HEALTH_EVENT_ATTRIBUTES.TIMESTAMP] = str(int(time.time()))
        self.header[HEALTH_EVENT_ATTRIBUTES.EVENT_ID] =  \
            self.header[HEALTH_EVENT_ATTRIBUTES.TIMESTAMP] + \
            "_" + str(uuid.uuid4().hex)

        self.payload = {}
        self.payload[HEALTH_EVENT_ATTRIBUTES.SOURCE] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.CLUSTER_ID] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.SITE_ID] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.RACK_ID] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.STORAGESET_ID] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.NODE_ID] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.RESOURCE_TYPE] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.RESOURCE_ID] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.RESOURCE_STATUS] = None
        self.payload[HEALTH_EVENT_ATTRIBUTES.SPECIFIC_INFO] = {}

    def set_or_update_payload(self, _input):
        """
        Update payload values
        """
        for key in _input.keys():
            if key in list(self.payload.keys()):
                self.payload[key] = _input[key]
            else:
                self.payload[HEALTH_EVENT_ATTRIBUTES.SPECIFIC_INFO][key] \
                    = _input[key]
