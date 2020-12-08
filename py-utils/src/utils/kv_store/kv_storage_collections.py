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

import json, toml, yaml
from src.utils.kv_store.kv_storage import KvStorage


class JsonKvStorage(KvStorage):
    """  Represents a JSON File Storage """ 

    name = "json"

    def __init__(self, store_path):
        KvStorage.__init__(self, store_path)

    def _load(self):
        """ Reads from the file """
        with open(self._store_path, 'r') as f:
            return json.load(f)

    def _dump(self, data):
        """ Saves data onto the file """
        with open(self._store_path, 'w') as f:
            json.dump(data, f, indent=2)


class YamlKvStorage(KvStorage):
    """  Represents a YAML File Storage """ 

    name = "yaml"

    def __init__(self, store_path):
        KvStorage.__init__(self, store_path)

    def _load(self):
        """ Reads from the file """
        with open(self._store_path, 'r') as f:
            return yaml.safe_load(f)

    def _dump(self, data):
        with open(self._store_path, 'w') as f:
            yaml.dump(data, f)


class TomlKvStorage(KvStorage):
    """  Represents a TOML File Storage """ 

    name = "toml"

    def __init__(self, store_path):
        KvStorage.__init__(self, store_path)

    def _load(self):
        """ Reads from the file """
        with open(self._store_path, 'r') as f:
            return toml.load(f, dict)

    def _dump(self, data):
        """ Saves data onto the file """
        with open(self._store_path, 'w') as f:
            toml.dump(data, f)


class IniKvStorage(KvStorage):
    """  Represents a YAML File Storage """ 

    name = "ini"

    def __init__(self, store_path):
        self._config = configparser.ConfigParser()
        KvStorage.__init__(self, store_path)
        self._type = configparser.SectionProxy

    def _load(self):
        """ Reads from the file """
        self._config.read(self._store_path)
        return self._config

    def _dump(self, data):
        """ Saves data onto the file """
        with open(self._store_path, 'w') as f:
            data.write(f)


class DictKvStorage(KvStorage):
    """ Represents Dictionary Without file """ 

    name = "dict"

    def __init__(self, data={}):
        KvStorage.__init__(self, data)

    def load(self):
        """ Reads from the file """
        return self._store_path

    def dump(self, data):
        """ Saves data onto dictionary itself """
        self._store_path = data


class JsonMessageKvStorage(JsonKvStorage):
    """ Represents and In Memory JSON Message """

    name = "jsonmessage"

    def __init__(self, json_str):
        """ 
        Represents the Json Without FIle
        :param json_str: Json String to be processed :type: str
        """ 
        Json.__init__(self, json_str)

    def load(self):
        """ Load json to python Dictionary Object. Returns Dict """

        return json.loads(self._store_path)

    def dump(self, data: dict):
        """ Sets data after converting to json """
        self._store_path = json.dumps(data)


class TextKvStorage(KvStorage):
    """ Represents a TEXT File Storage """ 

    name = "text"

    def __init__(self, store_path):
        KvStorage.__init__(self, store_path)

    def _load(self):
        """ Loads data from text file """ 
        with open(self._store_path, 'r') as f:
            return f.read()

    def _dump(self, data):
        """ Dump the data to desired file or to the source """ 
        with open(self._store_path, 'w') as f:
            f.write(data)
