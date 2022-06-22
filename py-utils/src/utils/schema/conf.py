#!/usr/bin/env python3

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

import os
from cortx.utils.schema.payload import *

class Conf:
    """Represents conf file - singleton."""
    _payloads = {}

    @staticmethod
    def init():
        """Initializes data from conf file."""
        pass

    @staticmethod
    def load(index, doc, force=False):
        if not os.path.isfile('%s' %doc):
            raise Exception(-1, 'File %s does not exist' %doc)
        if index in Conf._payloads.keys():
            if force == False:
                raise Exception('index %s is already loaded')
            Conf.save(index)
        Conf._payloads[index] = Payload(doc)

    @staticmethod
    def get(index, key, default_val=""):
        """Obtain value for the given key."""
        return Conf._payloads[index].get(key) if Conf._payloads[index].get(key) is not None else default_val

    @staticmethod
    def set(index, key, val):
        """Sets the value into the conf for the given key."""
        Conf._payloads[index].set(key, val)

    @staticmethod
    def save(index=None):
        indexes = [x for x in _payloads.keys()] if index is None else index
        for index in indexes:
            Conf._payloads[index].dump()


class ConfSection:
    """Represents sub-section of config file."""

    def __init__(self, from_dict: dict):
        """
        Initialize ConfSection by dictionary object.

        :param dict from_dict: base dictionary to create object from its keys and values
        """
        for key, value in from_dict.items():
            if isinstance(value, dict):
                setattr(self, key, ConfSection(value))
            else:
                setattr(self, key, value)


class DebugConf:
    """
    Class which simplifies work with debug settings in debug mode:

    make easy check whether debug-mode is enabled and requested option is set
    to desired value
    """

    def __init__(self, debug_settings: ConfSection):
        """Initialize debug configuration instance by debug settings."""
        self._debug_settings = debug_settings

    def __getattr__(self, attr):
        return getattr(self._debug_settings, attr)

    @property
    def http_enabled(self):
        """Validates if debug mode is enabled and HTTP is chosen."""
        return self._debug_settings.enabled and self._debug_settings.http_enabled
