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

class KvStorage:
    """
    This Abstract class will serve as base for key-value storage/db.
    The classes will extend this and provide their implementation of
    get, set and delete.
    """

    def __init__(self):
        pass

    def get(self, key):
        pass

    def set(self, key, value):
        pass

    def delete(self, key):
        pass


class KvStore:
    """
    This class will take KvStorage implementation as input and be front facing
    to the consumer.
    """

    def __init__(self, kvStorage):
        self._storage = kvStorage

    def get(self, key):
        return self._storage.get(key)

    def set(self, key, value):
        return self._storage.set(key, value)

    def delete(self, key):
        return self._storage.delete(key)
