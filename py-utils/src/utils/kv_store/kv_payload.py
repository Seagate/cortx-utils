#!/bin/python3 

# CORTX Python common library.
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

import errno
import re
from cortx.utils.kv_store.error import KvError

class KvPayload:
    """ Dict based in memory representation of Key Value data """

    def __init__(self, data, delim='>'):
        """
        kvstore will be initialized at the time of load
        delim is used to split key into hierarchy, e.g. "k1>2" or "k1.k2"
        """
        self._data = data if data is not None else {}
        if len(delim) > 1:
            raise KvError(errno.EINVAL, "Invalid delim %s", delim)
        self._delim = delim
        self._keys = []
        self.refresh_keys()

    def get_data(self, format_type: str = None):
        if format_type == None:
            return self._data
        formatter = Formatter.get(format_type)
        return formatter.convert(self._data)

    def get_keys(self):
        return self._keys

    def refresh_keys(self):
        """ Refresh keys. Caller can overrite this """
        self._refresh_keys(self._data)

    def _refresh_keys(self, data, pkey: str = None):
        if type(data) == list:
            for i in range(len(data)):
                self._keys.append("%s[%d]" % (pkey, i))
        elif type(data) == dict:
            for key in data.keys():
                nkey = key if pkey is None else f"%s%s%s" % (pkey, self._delim,
                                                             key)
                if type(data[key]) not in [dict, list]:
                    self._keys.append(nkey)
                else:
                    self._refresh_keys(data[key], nkey)
        else:
            raise KvError(errno.ENOSYS, "Cant handle type %s", type(data))

    def _set(self, key: str, val: str, data: dict):
        k = key.split(self._delim, 1)

        # Check if key has index, if so identify index
        index = None
        ki = re.split(r'\W+', k[0])
        if len(ki) > 1:
            if len(ki[0].strip()) == 0:
                raise KvError(errno.EINVAL, "Invalid key name %s", ki[0])
            if not ki[1].isnumeric():
                raise KvError(errno.EINVAL,
                                   "Invalid key index for the key %s", ki[0])
            k[0], index = ki[0], int(ki[1])

        if k[0] not in data.keys():
            data[k[0]] = {}
        if index is not None:
            if k[0] not in data.keys() or type(data[k[0]]) != list:
                data[k[0]] = []
            # if index is more than list size, extend the list
            for i in range(len(data[k[0]]), index + 1):
                data[k[0]].append({})
            # if this is leaf node of the key
            if len(k) == 1:
                data[k[0]][index] = val
            else:
                # In case the value is string replace with {}
                if type(data[k[0]][index]) in [str, list]:
                    data[k[0]][index] = {}
                self._set(k[1], val, data[k[0]][index])
            return

        if len(k) == 1:
            # if this is leaf node of the key
            data[k[0]] = val
        else:
            # This is not the leaf node of the key, process intermediate node
            if type(data[k[0]]) in [str, list]:
                data[k[0]] = {}
            self._set(k[1], val, data[k[0]])

    def set(self, key: str, val: str):
        """ Updates the value for the given key in the dictionary """
        return self._set(key, val, self._data)

    def _get(self, key: str, data: dict) -> str:
        k = key.split(self._delim, 1)

        # Check if key has index, if so identify index
        index = None
        ki = re.split(r'\W+', k[0])
        if len(ki) > 1:
            print("### ", ki)
            if len(ki[0].strip()) == 0:
                raise KvError(errno.EINVAL, "Invalid key %s", ki[0])

            if not ki[1].isnumeric():
                raise KvError(errno.EINVAL,
                                   "Invalid key index for the key %s", ki[0])
            k[0], index = ki[0], int(ki[1])

        if k[0] not in data.keys():
            return None
        data1 = data[k[0]]
        if index is not None:
            if type(data[k[0]]) != list or index >= len(data[k[0]]):
                return None
            data1 = data[k[0]][index]

        # if this is leaf node of the key
        if len(k) == 1: return data1

        # This is not the leaf node of the key, process intermediate node
        return self._get(k[1], data1)

    def get(self, key: str) -> str:
        """ Obtain value for the given key """
        return self._get(key, self._data)

    def _delete(self, key: str, data: dict):
        k = key.split(self._delim, 1)

        index = None
        ki = re.split(r'\W+', k[0])
        if len(ki) > 1:
            k[0], index = ki[0], int(ki[1])

        if k[0] not in data.keys():
            return None

        if index is not None:
            if type(data[k[0]]) != list:
                raise KvError(errno.EINVAL, "Invalid key %s", key)
            if index >= len(data[k[0]]):
                return
            if len(k) == 1:
                del data[k[0]][index]
            else:
                self._delete(k[1], data[k[0]][index])
            return

        if len(k) == 1:
            del data[k[0]]
        else:
            self._delete(k[1], data[k[0]])

    def delete(self, key):
        """ Deletes given set of keys from the dictionary """
        return self._delete(key, self._data)
