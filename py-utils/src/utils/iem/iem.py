#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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

import errno
from cortx.utils.iem.error import IemError


class Iem:
    """ IEM Framework over Message Bus """

    _check_none_values = True

    # RANGE/VALID VALUES for IEC Components
    # NOTE: RANGE VALUES are in hex number system.
    _SEVERITY_LEVELS = ["A", "X", "E", "W", "N", "C", "I", "D", "B"]
    _SOURCE_IDS = ["S", "H", "F", "O"]
    _HEX_BASE = 16
    _ID_MIN = "1"
    _COMPONENT_ID_MAX = "100"
    _MODULE_ID_MAX = "100"
    _EVENT_ID_MAX = "2710"

    def __init__(self, severity: str = None, source_id: str = None, \
        component_id: str = None, module_id: str = None, event_id: str = None, \
        message: str = None, **params):

        self._none_values = []
        self._severity = severity
        self._source_id = source_id
        self._component_id = component_id
        self._module_id = module_id
        self._event_id = event_id
        self._message = message
        self._params = params

        for attributes in ['_severity', '_source_id', '_component_id', '_module_id', \
            '_event_id', '_message']:
            self._none_values.append(None) if getattr(self, attributes) is \
                None else self._none_values.append(getattr(self, attributes))

        if not all(values is None for values in self._none_values):
            if any(values is None for values in self._none_values):
                raise IemError(errno.EINVAL, "Some IEM attributes are missing")
            self._check_none_values = False

            if self._severity not in self._SEVERITY_LEVELS:
                raise IemError(errno.EINVAL, "Invalid severity level. %s: ", \
                    self._severity)

            if self._source_id not in self._SOURCE_IDS:
                raise IemError(errno.EINVAL, "Invalid source_id type. %s: ", \
                    self._source_id)

            # Convert min and max range from hex to int
            min_id = int(self._ID_MIN, self._HEX_BASE)
            max_component_id = int(self._COMPONENT_ID_MAX, self._HEX_BASE)
            max_module_id = int(self._MODULE_ID_MAX, self._HEX_BASE)
            max_event_id = int(self._EVENT_ID_MAX, self._HEX_BASE)

            self.validate(self, min_id, ['_component_id', '_module_id', \
                '_event_id'], [max_component_id, max_module_id, max_event_id])

    def set(self, severity: str, source_id: str, component_id: str, \
        module_id: str, event_id: str, message: str, **params):

        self.__init__(severity, source_id, component_id, module_id, event_id, \
            message, **params)

    @staticmethod
    def validate(obj: object, min_id: int, attributes: list, max_ids: list):
        """ Validate IEC attributes """
        # Convert components from hex to int for comparison
        from collections import OrderedDict
        validate_attributes = OrderedDict()
        for ids in attributes:
            try:
                validate_attributes[ids] = int(getattr(obj, ids), obj._HEX_BASE)
            except Exception as e:
                raise IemError(errno.EINVAL, "Invalid hex value. %s", e)

        # Check if values are out of range
        for keys, max_values in zip(validate_attributes.keys(), max_ids):
            if validate_attributes[keys] not in range(min_id, max_values + 1):
                raise IemError(errno.EINVAL, "%s %s is not in range ", \
                    keys, getattr(obj, keys))

    def print_iem(self):
        """ Print IEM attributes """
        iem_attributes = {}
        for attributes in ['_severity', '_source_id', '_component_id', \
            '_module_id', '_event_id', '_message', '_params']:
            iem_attributes[attributes] = getattr(self, attributes)
        print(iem_attributes)