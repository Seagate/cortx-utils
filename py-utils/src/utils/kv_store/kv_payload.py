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
from cortx.utils.schema import Format


class KvPayload:
    """ Dict based in memory representation of Key Value data """

    def __init__(self, data=None, delim='>'):
        """
        kvstore will be initialized at the time of load
        delim is used to split key into hierarchy, e.g. "k1>2" or "k1.k2"
        """
        self._data = data if data is not None else {}
        if len(delim) > 1:
            raise KvError(errno.EINVAL, "Invalid delim %s", delim)
        self._delim = delim
        self._keys = []
        self._get_keys(self._keys, self._data)

    @property
    def json(self):
        return Format.dump(self._data, 'json')

    def get_data(self, format_type: str = None):
        if format_type == None:
            return self._data
        return Format.dump(self._data, format_type)

    def get_keys(self, **filters) -> list:
        """
        Obtains list of keys stored in the payload
        Input Paramters:
        Filters - Filters to be applied before the keys to be returned.
                  List of filters:
                  * key_index={True|False} (default: True)
                    when True, returns keys including array index
                    e.g. In case of "xxx[0],xxx[1]", only "xxx" is returned
        """
        if len(filters.items()) == 0:
            return self._keys
        keys = []
        self._get_keys(keys, self._data, None, **filters)
        return keys

    def _get_keys(self, keys: list, data, pkey: str = None,
        key_index: bool = True) -> None:
        if isinstance(data, list):
            if key_index == True:
                for i in range(len(data)):
                    keys.append("%s[%d]" % (pkey, i))
            else:
                keys.append(pkey)
        elif isinstance(data, dict):
            for key in data.keys():
                nkey = key if pkey is None else "%s%s%s" % (pkey, self._delim,
                                                            key)
                if not isinstance(data[key], (dict, list)):
                    keys.append(nkey)
                else:
                    self._get_keys(keys, data[key], nkey, key_index)
        else:
            raise KvError(errno.ENOSYS, "Cant handle type %s", type(data))

    def _set(self, key: str, val: str, data: dict):
        k = key.split(self._delim, 1)

        # Check if key has index, if so identify index
        index = None
        ki = re.split(r'\[([0-9]+)\]', k[0])
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
            if k[0] not in data.keys() or not isinstance(data[k[0]], list):
                data[k[0]] = []
            # if index is more than list size, extend the list
            for i in range(len(data[k[0]]), index + 1):
                data[k[0]].append({})
            # if this is leaf node of the key
            if len(k) == 1:
                data[k[0]][index] = val
            else:
                # In case the value is string replace with {}
                if isinstance(data[k[0]][index], (str, list)):
                    data[k[0]][index] = {}
                self._set(k[1], val, data[k[0]][index])
            return

        if len(k) == 1:
            # if this is leaf node of the key
            data[k[0]] = val
        else:
            # This is not the leaf node of the key, process intermediate node
            if isinstance(data[k[0]], (str, list)):
                data[k[0]] = {}
            self._set(k[1], val, data[k[0]])

    def set(self, key: str, val: str):
        """ Updates the value for the given key in the dictionary """
        self._set(key, val, self._data)
        if key not in self._keys:
            self._keys.append(key)

    def __setitem__(self, key: str, val: str):
        """ set operator for KV payload, i.e. kv['xxx'] = 'yyy' """
        self.set(key, val)

    def _get(self, key: str, data: dict) -> str:
        k = key.split(self._delim, 1)

        # Check if key has index, if so identify index
        index = None
        ki = re.split(r'\[([0-9]+)\]', k[0])
        if len(ki) > 1:
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
            if not isinstance(data[k[0]], list) or index >= len(data[k[0]]):
                return None
            data1 = data[k[0]][index]

        # if this is leaf node of the key
        if len(k) == 1: return data1

        # This is not the leaf node of the key, process intermediate node
        return self._get(k[1], data1)

    def get(self, key: str) -> str:
        """ Obtain value for the given key """
        return self._get(key, self._data)

    def __getitem__(self, key: str, val: str):
        """ read operator for KV payload, i.e. kv['xxx'] """
        return self.get(key)

    def _delete(self, key: str, data: dict):
        k = key.split(self._delim, 1)

        index = None
        ki = re.split(r'\[([0-9]+)\]', k[0])
        if len(ki) > 1:
            k[0], index = ki[0], int(ki[1])

        if k[0] not in data.keys():
            return False

        if index is not None:
            if not isinstance(data[k[0]], list):
                raise KvError(errno.EINVAL, "Invalid key %s", key)
            if index >= len(data[k[0]]):
                return False
            if len(k) == 1:
                del data[k[0]][index]
                return True
            else:
                return self._delete(k[1], data[k[0]][index])

        if len(k) == 1:
            del data[k[0]]
            return True
        else:
            return self._delete(k[1], data[k[0]])

    def delete(self, key) -> bool:
        """
        Deletes given set of keys from the dictionary
        Return Value:
        returns True if key existed/deleted. Returns False if key not found.
        """
        rc = self._delete(key, self._data)
        if rc == True and key in self._keys:
            del self._keys[self._keys.index(key)]
        return rc
