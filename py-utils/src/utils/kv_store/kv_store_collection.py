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

import os
import json, toml, yaml, configparser
from json.decoder import JSONDecodeError
from cortx.utils.process import SimpleProcess
from cortx.utils.kv_store.kv_store import KvStore


class JsonKvStore(KvStore):
    """  Represents a JSON File Store """

    name = "json"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)
        if not os.path.exists(self._store_path):
            with open(self._store_path, 'w+') as f:
                pass

    def load(self) -> dict:
        """ Reads from the file """
        data = {}
        with open(self._store_path, 'r') as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                pass
        return data

    def dump(self, data) -> None:
        """ Saves data onto the file """
        with open(self._store_path, 'w') as f:
            json.dump(data, f, indent=2)


class YamlKvStore(KvStore):
    """  Represents a YAML File Store """

    name = "yaml"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)

    def load(self) -> dict:
        """ Reads from the file """
        with open(self._store_path, 'r') as f:
            return yaml.safe_load(f)

    def dump(self, data) -> None:
        with open(self._store_path, 'w') as f:
            yaml.dump(data, f)


class TomlKvStore(KvStore):
    """  Represents a TOML File Store """

    name = "toml"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)

    def load(self) -> dict:
        """ Reads from the file """
        with open(self._store_path, 'r') as f:
            return toml.load(f, dict)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        with open(self._store_path, 'w') as f:
            toml.dump(data, f)


class IniKvStore(KvStore):
    """  Represents a YAML File Store """

    name = "ini"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)
        self._config = configparser.ConfigParser()
        self._type = configparser.SectionProxy

    def load(self) -> dict:
        """ Reads from the file """
        self._config.read(self._store_path)
        return self._config

    def dump(self, data) -> None:
        """ Saves data onto the file """
        with open(self._store_path, 'w') as f:
            data.write(f)


class DictKvStore(KvStore):
    """ Represents Dictionary Without file """

    name = "dict"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)

    def load(self) -> dict:
        """ Reads from the file """
        return self._store_path

    def dump(self, data) -> None:
        """ Saves data onto dictionary itself """
        self._store_path = data


class JsonMessageKvStore(JsonKvStore):
    """ Represents and In Memory JSON Message """

    name = "jsonmessage"

    def __init__(self, store_loc, store_path):
        """ 
        Represents the Json Without FIle
        :param json_str: Json String to be processed :type: str
        """
        JsonKvStore.__init__(self, store_loc, store_path)

    def load(self) -> dict:
        """ Load json to python Dictionary Object. Returns Dict """
        return json.loads(self._store_path)

    def dump(self, data: dict) -> None:
        """ Sets data after converting to json """
        self._store_path = json.dumps(data)


class TextKvStore(KvStore):
    """ Represents a TEXT File Store """

    name = "text"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)

    def load(self) -> dict:
        """ Loads data from text file """
        with open(self._store_path, 'r') as f:
            return f.read()

    def dump(self, data) -> None:
        """ Dump the data to desired file or to the source """
        with open(self._store_path, 'w') as f:
            f.write(data)


class PillarStore(KvStore):
    """ Salt Pillar based KV Store """
    name = "salt"

    def __init__(self, store_loc, store_path):
        KvStore.__init__(self, store_loc, store_path)

    def get(self, key):
        """Get pillar data for key."""
        cmd = f"salt-call pillar.get {key} --out=json"
        cmd_proc = SimpleProcess(cmd)
        out, err, rc = cmd_proc.run()

        if rc != 0:
            if rc == 127: err = f"salt command not found"
            raise KvError(rc, f"Cant get data for %s. %s.", key, err)

        res = None
        try:
            res = json.loads(out)
            res = res['local']

        except Exception as ex:
            raise KvError(errno.ENOENT, f"Cant get data for %s. %s.", \
                          key, ex)

        if res is None:
            raise KvError(errno.ENOENT, f"Cant get data for %s. %s." \
                                        f"Key not present")

        return res

    def set(self, key, value):
        # TODO: Implement
        pass

    def delete(self, key):
        # TODO: Implement
        pass
