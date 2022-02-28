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

import errno
import json
import time
import uuid
from kv_payload import KvPayload
from error import KvError
from const import HealthAttr, EventAttr

VERSION = "1.0"


class Event(KvPayload):
    """
    Class for health status event message schema,
    where producer can import this class object and add it
    in there existing schema.
    """

    def __init__(self):
        super().__init__()
        now = str(int(time.time()))
        _uuid = str(uuid.uuid4().hex)
        self.set(f'header>{HealthAttr.VERSION.value}', VERSION)
        self.set(f'header>{HealthAttr.TIMESTAMP.value}', now)
        self.set(f'header>{HealthAttr.EVENT_ID.value}', now + _uuid)

        for key in [HealthAttr.SOURCE, HealthAttr.CLUSTER_ID,
                    HealthAttr.SITE_ID, HealthAttr.RACK_ID,
                    HealthAttr.STORAGESET_ID, HealthAttr.NODE_ID,
                    HealthAttr.RESOURCE_TYPE,
                    HealthAttr.RESOURCE_STATUS,
                    ]:
            self.set(f'payload>{key.value}', None)

        self.set(f'payload>{HealthAttr.SPECIFIC_INFO.value}', {})

    def set_payload(self, payload: KvPayload):
        for key in payload.get_keys():
            self.set(f'payload>{key}', payload.get(key))
 
    def get_payload(self):
        return self.get('payload')

    def get_event(self):
        """
        Return dictionary attribute.
        """
        return self.json
