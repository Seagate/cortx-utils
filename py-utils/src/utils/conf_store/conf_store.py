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

from cortx.utils.conf_store.error import ConfStoreError
from cortx.utils.conf_store.conf_cache import ConfCache
from cortx.utils.kv_store.kv_store import KvStoreFactory


class ConfStore:
    """ Configuration Store based on the KvStore """

    def __init__(self):
        """ kvstore will be initialized at the time of load """
        self._cache = {}

    def load(self, index: str, kvs_url: str, overwrite=False, callback=None):
        """
        Loads the config from KV Store

        Parameters:
        index:     Identifier for the config loaded from the KV Store
        kv_store:  KV Store (Conf Backend)
        overwrite: When False, it throws exception if index already exists. 
                   Default: False 
        callback:  Callback for the config changes in the KV Sto
        """
        if index in self._cache.keys() and not overwrite: 
            raise ConfStoreError(errno.EINVAL, "conf index %s already exists",
                index)

        kv_store = KvStoreFactory.get_instance(kvs_url)
        self._cache[index] = ConfCache(kv_store)

    def save(self, index: str):
        """ Saves the given index configuration onto KV Store """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                index)

        self._cache[index].dump()

    def get(self, index: str, key: str, default_val=None):
        """
        Obtain value for the given configuration

        Paraeters:
        index   Configuration Domain ID where config key values are stored
        key     Configuration key. This can take two forms
                1. "xyz" - Top Level Key
                2. "x.y.z" - Key 'z' under x and y. Nested Structure.
        default_val
                Default Value

        Return Value:
                Return type will be dict or string based of key
        """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                                 index)
        if key is None:
            raise ConfStoreError(errno.EINVAL, "can't able to find config key "
                                               "%s in loaded config", key)
        val = self._cache[index].get(key)
        return default_val if val is None else val

    def set(self, index: str, key: str, val):
        """
        Sets the value into the DB for the given index, key

        Parameters:
        index   Configuration Domain ID where config key values are stored
        key     Configuration key. This can take two forms
                1. "xyz" - Top Level Key
                2. "x.y.z" - Key 'z' under x and y. Nested Structure.
        val     Value to be set. Can be string or dict
        """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                index)

        self._cache[index].set(key, val)

    def get_keys(self, index: str):
        """ Obtains list of keys stored in the specific config store """
        return self._cache[index].get_keys()

    def get_data(self, index: str):
        """ Obtains entire config for given index """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                                 index)
        return self._cache[index].get_data()

    def delete(self, index: str, key: str):
        """ Delets a given key from the config """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                index)

        self._cache[index].delete(key)

    def copy(self, src_index: str, dst_index: str, key_list: list = None):
        """
        Copies one config domain to the other and saves
        
        Parameters:
        src_index Source Index 
        dst_index Destination Index 
        """
        if src_index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                src_index)

        if dst_index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                dst_index)

        if key_list is None:
            key_list = self._cache[src_index].get_keys()
        for key in key_list:
            self._cache[dst_index].set(key, self._cache[src_index].get(key))


class Conf:
    """ Singleton class instance based on conf_store """
    _conf = None

    @staticmethod
    def load(index: str, url: str):
        """ Loads Config from the given URL """
        if Conf._conf is None: Conf._conf = ConfStore()
        Conf._conf.load(index, url)

    @staticmethod
    def save(index: str):
        """ Saves the configuration onto the backend store """
        Conf._conf.save(index)

    @staticmethod
    def set(index: str, key: str, val):
        """ Sets config value for the given key """
        Conf._conf.set(index, key, val)

    @staticmethod
    def get(index: str, key: str):
        """ Obtains config value for the given key """
        return Conf._conf.get(index, key)

    @staticmethod
    def delete(index: str, key: str):
        """ Deletes a given key from the config """
        Conf._conf.delete(index, key)

    @staticmethod
    def copy(src_index: str, dst_index: str, key_list: list = None):
        """ Creates a Copy suffixed file for main file"""
        Conf._conf.copy(src_index, dst_index, key_list)
        Conf._conf.save(dst_index)

    @staticmethod
    def get_keys(index: str):
        """ Obtains list of keys stored in the specific config store """
        return Conf._conf.get_keys(index)