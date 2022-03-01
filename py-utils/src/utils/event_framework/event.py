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

import time
import uuid
from enum import Enum
from cortx.utils.kv_store.kv_payload import KvPayload


class Attr(Enum):
    def __str__(self):
        return '%s' % self.value

class EventAttr(Attr):
    """Enum class to define constants for event attributes."""

    EVENT_HEADER    = 'header'
    EVENT_PAYLOAD   = 'payload'
    VERSION         = 'version'
    TIMESTAMP       = 'timestamp'
    EVENT_ID        = 'event_id'

VERSION = "1.0"

class Event(KvPayload):
    """Base class for event message schema."""

    def __init__(self, payload: KvPayload = KvPayload()):
        super().__init__()
        # Set Header
        _now = str(time.time())
        _uuid = str(uuid.uuid4().hex)
        super().set(f'header>{EventAttr.VERSION.value}', VERSION)
        super().set(f'header>{EventAttr.TIMESTAMP.value}', _now)
        super().set(f'header>{EventAttr.EVENT_ID.value}', _now + _uuid)
        # Set payload if required
        for key in payload.get_keys():
            super().set(f'payload>{key}', payload.get(key))

    def set_payload(self, payload: KvPayload):
        for key in payload.get_keys():
            super().set(f'payload>{key}', payload.get(key))

    def set_payload_attr(self, key, val):
        super().set(f'payload>{key}', val)
