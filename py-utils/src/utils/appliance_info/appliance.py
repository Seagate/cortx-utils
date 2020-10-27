# CORTX-Py-Utils: CORTX Python common library.
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

from cortx.utils.schema.payload import CommonPayload
from cortx.utils.log import Log

class ApplianceInfo:
    """
    This class handles information related to CORTX appliance like serial number etc.
    """
    _type = dict

    def __init__(self, file_path):
        self._file_path = file_path
        self._appliance_obj = None
        self._data = None
        self._appliance_obj = CommonPayload(self._file_path)

    def load(self):
        """
        This method will create an in-memory object from the appliance JSON file.
        """
        self._data = self._appliance_obj.load()

    def _get(self, key, data):
        """
        Recursively obtains the value for the given key
        """
        new_key = key.split('.', 1)
        if new_key[0] not in data.keys(): return None
        return self._get(new_key[1], data[new_key[0]]) if len(new_key) > 1 else data[new_key[0]]

    def get(self, key=None):
        """
        This method fetches the appliance info JSON. If key is provided it
        returns its value otherwise the whole doc is returned.
        """
        ret = None
        try:
            if key:
                ret = self._get(key, self._data)
            else:
                ret = self._data
        except Exception as ex:
            Log.error(f"Error in getting the appliance info. {ex}")
        return ret

    def _set(self, key, val, data):
        """
        This method recursively searches for the key and sets the value specified.
        """
        new_key = key.split('.', 1)
        if len(new_key) == 1:
            data[new_key[0]] = val
            return
        if new_key[0] not in data.keys() or type(data[new_key[0]]) != self._type:
            data[new_key[0]] = {}
        self._set(new_key[1], val, data[new_key[0]])

    def set(self, key, value):
        """
        This method sets the in-memory value based on the key provided.
        """
        try:
            self._set(key, value, self._data)
        except Exception as ex:
            Log.error(f"Error in setting the appliance info. {ex}")

    def save(self, data):
        """
        This method saves the in-memory aplliannce info to a physical JSON
        """
        self._appliance_obj.dump(data)
