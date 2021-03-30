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

import configparser
import errno
import os

from cortx.utils.kv_store.error import KvError
from cortx.utils.kv_store.kv_store import KvStore
from cortx.utils.kv_store.kv_payload import KvPayload
from cortx.utils.process import SimpleProcess
from cortx.utils.schema import Format


class JsonKvStore(KvStore):
    """ Represents a JSON File Store """

    name = "json"

    def __init__(self, store_loc, store_path, delim='>'):
        import json
        KvStore.__init__(self, store_loc, store_path, delim)
        if not os.path.exists(self._store_path):
            with open(self._store_path, 'w+') as f:
                json.dump({}, f, indent=2)

    def load(self) -> KvPayload:
        """ Reads from the file """
        import json
        from json.decoder import JSONDecodeError
        data = {}
        with open(self._store_path, 'r') as f:
            try:
                data = json.load(f)
            except JSONDecodeError as jerr:
                raise KvError(errno.EINVAL, "Invalid JSON format %s",
                                   jerr.__str__())
        return KvPayload(data, self._delim)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        import json
        with open(self._store_path, 'w') as f:
            json.dump(data.get_data(), f, indent=2)


class YamlKvStore(KvStore):
    """ Represents a YAML File Store """

    name = "yaml"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        if not os.path.exists(self._store_path):
            with open(self._store_path, 'w+') as f:
                pass

    def load(self) -> KvPayload:
        """ Reads from the file """
        import yaml
        with open(self._store_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except Exception as yerr:
                raise KvError(errno.EINVAL, "Invalid YAML format %s",
                                   yerr.__str__())
        return KvPayload(data, self._delim)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        import yaml
        with open(self._store_path, 'w') as f:
            yaml.dump(data.get_data(), f, default_flow_style=False)


class TomlKvStore(KvStore):
    """ Represents a TOML File Store """

    name = "toml"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        if not os.path.exists(self._store_path):
            with open(self._store_path, 'w+') as f:
                pass

    def load(self) -> KvPayload:
        """ Reads from the file """
        import toml
        with open(self._store_path, 'r') as f:
            try:
                data = toml.load(f, dict)
            except Exception as terr:
                raise KvError(errno.EINVAL, "Invalid TOML format %s",
                                   terr.__str__())
        return KvPayload(data, self._delim)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        import toml
        with open(self._store_path, 'w') as f:
            toml.dump(data.get_data(), f)


class IniKvPayload(KvPayload):
    """ In memory representation of INI conf data """
    def __init__(self, configparser, delim='>'):
        super().__init__(configparser, delim)

    def refresh_keys(self):
        self._keys = []
        for section in self._data.sections():
            for key in [option for option in self._data[section]]:
                self._keys.append(f"{section}>{key}")

    def set(self, key, val):
        k = key.split('>', 1)
        if len(k) <= 1:
            raise KvError(errno.EINVAL, "Missing section in key %s", \
                key)

        self._data[k[0]][k[1]] = val
        if key not in self._keys:
            self._keys.append(key)

    def get(self, key):
        k = key.split('>', 1)
        if len(k) <= 1:
            raise KvError(errno.EINVAL, "Missing section in key %s", \
                key)
        return self._data[k[0]][k[1]]

    def delete(self, key):
        k = key.split('>', 1)
        if len(k) == 1:
            self._data.remove_section(k[0])
        elif len(k) == 2:
            self._data.remove_option(k[0], k[1])
        if key in self._keys: self._keys.remove(key)


class IniKvStore(KvStore):
    """ Represents a Ini File Store """

    name = "ini"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        self._config = configparser.ConfigParser()
        self._type = configparser.SectionProxy

    def load(self) -> IniKvPayload:
        """ Reads from the file """
        try:
            self._config.read(self._store_path)
        except Exception as err:
            raise KvError(errno.EINVAL, "Invalid INI format %s",
                               err.__str__())
        return IniKvPayload(self._config, self._delim)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        config = data.get_data()
        with open(self._store_path, 'w') as f:
            config.write(f)


class DictKvStore(KvStore):
    """ Represents Dictionary Without file """

    name = "dict"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)

    def load(self) -> KvPayload:
        """ Reads from the file """
        return KvPayload(self._store_path, self._delim)

    def dump(self, data) -> None:
        """ Saves data onto dictionary itself """
        self._store_path = data.get_data()


class JsonMessageKvStore(JsonKvStore):
    """ Represents and In Memory JSON Message """

    name = "jsonmessage"

    def __init__(self, store_loc, store_path, delim='>'):
        """
        Represents the Json Without FIle
        :param json_str: Json String to be processed :type: str
        """
        JsonKvStore.__init__(self, store_loc, store_path, delim)

    def load(self) -> KvPayload:
        """ Load json to python Dictionary Object. Returns Dict """
        import json
        return KvPayload(json.loads(self._store_path), self._delim)

    def dump(self, data: dict) -> None:
        """ Sets data after converting to json """
        import json
        self._store_path = json.dumps(data.get_data())


class PropertiesKvStore(KvStore):
    """ Represents a Properties File Store """

    name = "properties"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)

    def load(self) -> KvPayload:
        """ Loads data from properties file """
        data = {}
        with open(self._store_path, 'r') as f:
            try:
                for line in f.readlines():
                    line = line.strip()
                    if not line or line[0] == '#':
                        continue
                    key, val = line.split('=', 1)
                    data[key.strip()] = val.strip()
            except Exception as ex:
                raise KvError(errno.ENOENT, "Invalid properties store format %s. %s.", line, ex)
        return KvPayload(data, self._delim)

    def dump(self, data) -> None:
        """ Dump the data to desired file or to the source """
        kv_list = data.get_data()
        with open(self._store_path, 'w') as f:
            for key, val in kv_list.items():
                f.write("%s = %s\n" %(key, val))


class PillarKvStore(KvStore):
    """ Salt Pillar based KV Store """
    name = "pillar"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        from salt.client import LocalClient
        self._target = '*'
        self._pillar_root = "/srv/pillar/"
        self._client = LocalClient()
        self._set_pillar_target_and_location()
        self._delim = delim

    def _set_pillar_target_and_location(self) -> None:
        """
        self._tragets are required to run a slat command.
        self._pillar_root is pillar location from where the kvstore generated
        sls files need to be stored
        """
        loc_arg = self._store_path.split("@")
        target = self._client.cmd("*", "test.ping")
        valid_target = [key for key, value in target.items() if value is True]
        if len(loc_arg) > 1 and (not loc_arg[1] or loc_arg[1] not in valid_target):
            raise KvError(errno.ENOENT, "Invalid target node %s.", loc_arg[1])
        if len(loc_arg) > 1:
            self._target = loc_arg[1]
        # Set pillar root so that kvstore generated files will be kept there
        if not os.path.exists(loc_arg[0]):
            raise KvError(errno.ENOENT, "Invalid pillar path %s", self._store_loc)
        self._pillar_root = loc_arg[1]

    def load(self) -> KvPayload:
        """ Loads data from pillar store """
        try:
            res = self._client.cmd(self._target, 'pillar.items')
        except Exception as err:
            raise KvError(errno.ENOENT, "Cant load data %s.", err)
        return KvPayload(res, self._delim)

    def dump(self, data:dict) -> None:
        """ Saves data onto the file """
        import yaml
        raw_data = data.get_data()
        target_nodes = self._client.cmd("*", "test.ping")
        for each_node in raw_data:
            if each_node in target_nodes:
                sls_data_list = raw_data[each_node]
                for each_key in sls_data_list:
                    data = Format.dump({each_key:sls_data_list[each_key]}, "yaml")
                    with open(f"{self._pillar_root}{each_key}.sls", 'w+') as f:
                        yaml.dump(yaml.safe_load(data), f, default_flow_style=False)
