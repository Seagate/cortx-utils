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

from cortx.utils.conf_store.conf_cache import ConfCache


class ConfStore:
    """
    ConfStore implements configuration management on top of KvStore
    """
    def __init__(self):
        """
        kvstore will be initialized at the time of load
        """
        self.kvstore = ''
        self._payload = {}

    def load(self, index, kvStore, force=False, callback=None):
        """
        Args:
            index (str): named key of the loaded value in the ConfCache
            kvStore (object): instance of KvStorageFactory
            force (bool): optional
            callback (): W.I.P
        """
        if hasattr(kvStore, 'name'):
            if (index in self._payload.keys() and force) or index not in self._payload.keys():
                self._payload[index] = ConfCache(kvStore)
            else:
                raise Exception('index %s is already loaded')
        else:
            raise Exception('kvStore value should be instance of kvStoreFactory')

    def get(self, index, key=None, default_value=None):
        """
        Args:
            index (str): named key of the loaded value in the ConfCache
            key (str): optional. key for the value to be retrieved.
            key will be chained with '.' to denote nested structure.
            eg. project.team.dev.name
            default_value (dict) : optional. W.I.P
        """
        if key is not None:
            return self._payload[index].get(key) if self._payload[index].get(key) is not None else default_value
        else:
            return self._payload[index].load() if self._payload[index] is not None else default_value

    def set(self, index, keyList, valueList):
        #Todo: WIP
        """
        Args:
            index (str): named key of the loaded value in the ConfCache
            keyList (list): list of key's. Need to be iterated and stored.
            valueList (list): list of value's, Need to be iterated and stored based of keylist.
        """
        pass

    def copy(self):
        # Todo: WIP
        pass

    def merge(self):
        # Todo: WIP
        pass

    def save(self, index=None):
        # Todo: WIP
        """
        Args:
            index (str): optional. named key to state which value need to be writen to the file.
            If index is None then to save all the configurations.
        """
        pass

    def backup(self):
        # Todo: WIP
        pass
