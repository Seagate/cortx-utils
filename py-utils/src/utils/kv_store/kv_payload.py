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

    def __init__(self, data: dict = None, delim='>', recurse: bool = True):
        """
        kvstore will be initialized at the time of load
        delim is used to split key into hierarchy, e.g. "k1>2" or "k1.k2"
        """
        self._data = data if data is not None else {}
        if len(delim) > 1:
            raise KvError(errno.EINVAL, "Invalid delim %s", delim)
        self._delim = delim
        self._keys = []
        if recurse:
            self._get_keys(self._keys, self._data)
        else:
            self._shallow_get_keys(self._keys, self._data)

    @property
    def json(self):
        return Format.dump(self._data, 'json')

    def get_data(self, format_type: str = None):
        if format_type == None:
            return self._data
        return Format.dump(self._data, format_type)

    def get_keys(self, recurse: bool = True, **filters) -> list:
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
        if recurse:
            self._get_keys(keys, self._data, None, **filters)
        else:
            self._shallow_get_keys(keys, self._data, None, **filters)
        return keys

    def _get_keys(self, keys: list, data, pkey: str = None,
        key_index: bool = True) -> None:
        if isinstance(data, list):
            for index, d in enumerate(data):
                index_suffix = f"[{index}]" if key_index else ""
                if isinstance(d, dict):
                    newkey = None if not pkey else "%s%s" % (pkey, index_suffix)
                    self._get_keys(keys, d, newkey, key_index)
                elif isinstance(d, (str, int)):
                    newkey = "%s%s" % (pkey, index_suffix)
                    if newkey not in keys:
                        keys.append(newkey)
        elif isinstance(data,  dict):
            for key, val in data.items():
                newkey = key if pkey is None else "%s%s%s" % (pkey, self._delim, key)
                if isinstance(val, (list, dict)):
                    self._get_keys(keys, val, newkey, key_index)
                elif isinstance(val, (str, int)):
                    if newkey not in keys:
                        keys.append(newkey)

    def _shallow_get_keys(self, keys: list, data, pkey: str = None,
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
                    self._shallow_get_keys(keys, data[key], nkey, key_index)
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

    def _key_index_split(self, indexed_key: str) -> list:
        """ Split index from key """
        return re.split(r'\[([0-9]+)\]', indexed_key)

    def _shallow_get(self, key: str, data: dict) -> str:
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
        return self._shallow_get(k[1], data1)

    def _get(self, key: str, data: dict) -> str:
        """ Core logic for get """
        # Indexed keys Validations can be put here for all methods
        key_split = key.split(self._delim, 1)

        # leaf node
        if len(key_split) == 1:
            [leaf_key] = key_split
            leaf_key_index = self._key_index_split(leaf_key)

            if len(leaf_key_index[0].strip()) == 0:
                raise KvError(errno.EINVAL, "Empyt key %s", leaf_key)
            if len(leaf_key_index) > 1:
                if not leaf_key_index[1].isnumeric():
                    raise KvError(errno.EINVAL, \
                        "Invalid key index for the key %s", leaf_key)
                if leaf_key_index[2]:
                    raise KvError(errno.EINVAL, "Invalid key %s", leaf_key)

                leaf_key, leaf_index = leaf_key_index[0], int(leaf_key_index[1])
                if leaf_key not in data.keys() or \
                    leaf_index > len(data[leaf_key])-1 or \
                    leaf_key not in data.keys() or \
                    not isinstance(data[leaf_key], list):
                    return None
                return data[leaf_key][leaf_index]

            if isinstance(data, dict):
                if leaf_key not in data.keys():
                    return None
                return data[leaf_key]
        elif len(key_split) > 1:
            p_key, c_key = key_split

        # Check if parent key has index, if so split key and index
        key_index = self._key_index_split(p_key)
        # Raise error if key is an empty str
        if len(key_index[0].strip()) == 0:
            raise KvError(errno.EINVAL, "Empyt key %s", p_key)

        if len(key_index) > 1:
            if not key_index[1].isnumeric():
                raise KvError(errno.EINVAL, \
                    "Invalid key index for the key %s", p_key)
            if key_index[2]:
                raise KvError(errno.EINVAL, "Invalid key %s", p_key)
            p_key, p_index = key_index[0], int(key_index[1])
            if isinstance(data[p_key], list):
                if p_index > (len(data[p_key])-1):
                    return None
                if isinstance(data[p_key][p_index], dict):
                    return self._get(c_key, data[p_key][p_index])
            else:
                # Index for a dict!
                return None
        else:
            if p_key not in data.keys():
                return None
            if isinstance(data[p_key], dict):
                return self._get(c_key, data[p_key])
            else:
                return None

    def get(self, key: str, recurse: bool = True) -> str:
        """ Obtain value for the given key """
        if recurse:
            return self._get(key, self._data)
        return self._shallow_get(key, self._data)

    def __getitem__(self, key: str):
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


class ConsulKvPayload:
    """ backend adapter for consul api """

    def __init__(self, consul, delim):
        self._consul = consul
        if len(delim) > 1:
            raise KvError(errno.EINVAL, "Invalid delim %s", delim)
        self._delim = delim

    def get(self, key: str) -> str:
        """ get value for consul key """
        index, data = self._consul.kv.get(key)
        if isinstance(data, dict):
            return data['Value'].decode()
        elif data is None:
            return None
        else:
            raise KvError(errno.EINVAL,
                          "Invalid response from consul: %d:%s", index, data)

    def set(self, key: str, val: str):
        """ set the value to the key in consul kv """
        return self._consul.kv.put(key, val)

    def delete(self, key: str):
        """ delete the key:value for the input key """
        return self._consul.kv.delete(key)

    def get_keys(self) -> list:
        """ Return a list of all the keys present"""
        keys =  self._consul.kv.get("", keys=True)[1]
        return keys

