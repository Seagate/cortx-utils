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

    def get(self, index: str, key: str, default_val=None,
            key_delimiter: str = None) -> str:
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
        key_delimiter : defines how to split the given key chain
        key1>key2 or key1.key2
        """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                                 index)
        if key is None:
            raise ConfStoreError(errno.EINVAL, "can't able to find config key "
                                               "%s in loaded config", key)
        ConfStore.check_key_delimiter(key_delimiter)
        val = self._cache[index].get(key, key_delimiter)
        return default_val if val is None else val

    def set(self, index: str, key: str, val, key_delimiter: str = None) -> None:
        """
        Sets the value into the DB for the given index, key

        Parameters:
        index   Configuration Domain ID where config key values are stored
        key     Configuration key. This can take two forms
                1. "xyz" - Top Level Key
                2. "x.y.z" - Key 'z' under x and y. Nested Structure.
        val     Value to be set. Can be string or dict
        key_delimiter : defines how to split the given key chain
        key1>key2 or key1.key2
        """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                index)

        ConfStore.check_key_delimiter(key_delimiter)

        self._cache[index].set(key, val, key_delimiter)

    def get_keys(self, index: str) -> list:
        """ Obtains list of keys stored in the specific config store """
        return self._cache[index].get_keys()

    def get_data(self, index: str) -> dict:
        """ Obtains entire config for given index """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                                 index)
        return self._cache[index].get_data()

    def delete(self, index: str, key: str, key_delimiter: str = None) -> None:
        """
        Delets a given key from the config
        key_delimiter : defines how to split the given key chain
        key1>key2 or key1.key2
        """
        if index not in self._cache.keys():
            raise ConfStoreError(errno.EINVAL, "config index %s is not loaded",
                index)
        ConfStore.check_key_delimiter(key_delimiter)

        self._cache[index].delete(key, key_delimiter)

    def copy(self, src_index: str, dst_index: str, key_list: list = None) \
            -> None:
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

    @staticmethod
    def check_key_delimiter(key_delimiter=None) -> None:
        delimiter_list = ['.', '|', '>', ',', ';', ':', '%', '#', '@', '/']
        if (key_delimiter is not None and
                (type(key_delimiter) is not str or key_delimiter.strip() == "")
                and key_delimiter not in delimiter_list):
            raise ConfStoreError(
                errno.EINVAL,
                "Key delimiter should be a type of str and also be either one "
                "of allowed '. | > , ; : %% # @ /' . Empty delimiters are not "
                "allowed %s try > or < or .",
                key_delimiter)


class Conf:
    """ Singleton class instance based on conf_store """
    _conf = None

    @staticmethod
    def load(index: str, url: str) -> None:
        """ Loads Config from the given URL """
        if Conf._conf is None: Conf._conf = ConfStore()
        Conf._conf.load(index, url)

    @staticmethod
    def save(index: str) -> None:
        """ Saves the configuration onto the backend store """
        Conf._conf.save(index)

    @staticmethod
    def set(index: str, key: str, val, key_delimiter: str = None) -> None:
        """ Sets config value for the given key """
        Conf._conf.set(index, key, val, key_delimiter=key_delimiter)

    @staticmethod
    def get(index: str, key: str, key_delimiter: str = None) -> str:
        """ Obtains config value for the given key """
        return Conf._conf.get(index, key, key_delimiter=key_delimiter)

    @staticmethod
    def delete(index: str, key: str, key_delimiter: str = None) -> None:
        """ Deletes a given key from the config """
        Conf._conf.delete(index, key, key_delimiter=key_delimiter)

    @staticmethod
    def copy(src_index: str, dst_index: str, key_list: list = None) -> None:
        """ Creates a Copy suffixed file for main file"""
        Conf._conf.copy(src_index, dst_index, key_list)
        Conf._conf.save(dst_index)

    @staticmethod
    def get_keys(index: str) -> list:
        """ Obtains list of keys stored in the specific config store """
        return Conf._conf.get_keys(index)
