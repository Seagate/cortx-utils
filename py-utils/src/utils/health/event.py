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
from cortx.utils.kv_store.kv_payload import KvPayload
from cortx.utils.kv_store.error import KvError
from cortx.utils.health.const import HealthAttr, EventAttr

VERSION = "1.0"


class Event(KvPayload):
    """
    Class for health status event message schema,
    where producer can import this class object and add it
    in there existing schema.
    """

    def __init__(self):
        super().__init__()
        event = KvPayload(delim='.')
        now = str(int(time.time()))
        _uuid = str(uuid.uuid4().hex)
        event.set(f'header.{HealthAttr.VERSION.value}', VERSION)
        event.set(f'header.{HealthAttr.TIMESTAMP.value}', now)
        event.set(f'header.{HealthAttr.EVENT_ID.value}', now + _uuid)

        for key in [HealthAttr.SOURCE, HealthAttr.CLUSTER_ID,
                    HealthAttr.SITE_ID, HealthAttr.RACK_ID,
                    HealthAttr.STORAGESET_ID, HealthAttr.NODE_ID,
                    HealthAttr.RESOURCE_TYPE,
                    HealthAttr.RESOURCE_STATUS]:
            event.set(f'payload.{key.value}', None)

        specific_info = KvPayload(delim='.')
        event.set(f'payload.{HealthAttr.SPECIFIC_INFO.value}', specific_info)

        self.set(f'event', event)

    def set_payload(self, payload: KvPayload):
        """
            Update payload values.
            params: payload data of attributes with value type : KvPayload
            e.g. payload = {"source" : "hare", "node_id" : "2"}
            it may be format of dict, json, yaml format.
        """
        for key in payload.keys():
            if key in list(self._data['event']._data['payload'].keys()):
                self._data['event']._data['payload'][key] = payload.get(key)
            else:
                raise KvError(errno.EINVAL, "Invalid key name %s", key)

    def ret_dict(self):
        """
        Return dictionary attribute.
        """
        return json.loads(json.dumps(self, default=lambda o: o.get_data()))
