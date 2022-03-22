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
import os
from typing import Union
from consul import Consul, ConsulException
from requests.exceptions import RequestException
from urllib.error import HTTPError
from configparser import ConfigParser, NoOptionError, NoSectionError

from cortx.utils.kv_store.error import KvError
from cortx.utils.kv_store.kv_store import KvStore
from cortx.utils.kv_store.kv_payload import KvPayload
from cortx.utils.process import SimpleProcess
from cortx.utils.common import ExponentialBackoff


class JsonKvStore(KvStore):
    """ Represents a JSON File Store """

    name = "json"

    def __init__(self, store_loc, store_path, delim='>'):
        import json
        KvStore.__init__(self, store_loc, store_path, delim)
        if not os.path.exists(self._store_path):
            with open(self._store_path, 'w+') as f:
                json.dump({}, f, indent=2)

    def load(self, **kwargs) -> KvPayload:
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
        recurse = True
        if 'recurse' in kwargs.keys():
            recurse = kwargs['recurse']
        return KvPayload(data, self._delim, recurse=recurse)

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

    def load(self, **kwargs) -> KvPayload:
        """ Reads from the file """
        import yaml
        with open(self._store_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except Exception as yerr:
                raise KvError(errno.EINVAL, "Invalid YAML format %s",
                                   yerr.__str__())
        recurse = True
        if 'recurse' in kwargs.keys():
            recurse = kwargs['recurse']
        return KvPayload(data, self._delim, recurse=recurse)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        import yaml
        with open(self._store_path, 'w') as f:
            yaml.dump(data.get_data(), f, default_flow_style=False)


class DirKvStore(KvStore):
    """ Organizes Key Values in a dir structure """
    name = "dir"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        if not os.path.exists(self._store_path):
            os.mkdir(self._store_path)

    def load(self, **kwargs):
        """ Return Empty Set. Cant read dir structure. Not supported """
        return KvPayload()

    def dump(self, payload: dict):
        """ Stores payload onto the store """
        keys = payload.get_keys()
        vals = [payload[key] for key in keys]
        self.set(keys, vals)

    def get_keys(self, key_prefix: str = None):
        """ Returns the list of keys starting with given prefix """
        _, key_file = self._get_key_path(key_prefix)
        if os.path.isfile(key_file):
            return [key_file.split("/").join(self._delim)]
        keys = []
        if key_prefix is None:
            key_prefix = ""
        else:
            key_prefix = "%s%s" %(key_prefix, self._delim)
        for root, _, file_names in os.walk(key_file):
            path = ""
            if root != key_file:
                path = root.replace(key_file+'/', '') + self._delim
            keys = [f'{key_prefix}{path}{f}' for f in file_names]
        return keys

    def get_data(self, format_type: str = None) -> dict:
        keys = self.get_keys()
        kv = {}
        for key in keys:
            kv[key] = self.get(key)
        return kv

    def set_data(self, payload: KvPayload):
        self.dump(payload)

    def _get_key_path(self, key):
        """ breaks key into dir path e.g. a>b>c to /root/a/b/c """
        if key is None:
            return self._store_path, self._store_path
        key_list = key.split(self._delim)
        key_dir = os.path.join(self._store_path, *key_list[0:-1])
        key_file = os.path.join(key_dir, key_list[-1])
        return key_dir, key_file

    def set(self, keys: list, vals: list):
        """ stores given keys and values into the store """
        if len(keys) != len(vals):
            raise KvError(errno.EINVAL, "Mismatched keys & values %s:%s",
                          keys, vals)

        for key, val in zip(keys, vals):
            key_dir, key_file = self._get_key_path(key)
            try:
                os.makedirs(key_dir, exist_ok = True)
            except Exception as e:
                raise KvError(errno.EACCES, "Cant set key %s. %s", key, e)
            if os.path.exists(key_file) and not os.path.isfile(key_file):
                raise KvError(errno.EINVAL, "Invalid Key %s" % key)
            with open(key_file, 'w') as f:
                f.write(val)

    def get(self, keys: list):
        """ Obtains values corresponding to the keys from the store """
        vals = []
        for key in keys:
            _, key_file = self._get_key_path(key)
            try:
                with open(key_file, 'r') as f:
                    vals.append(f.read())
            except OSError:
                vals.append(None)
        return vals

    def delete(self, keys: list):
        """ Deletes given set of keys from the store """
        for key in keys:
            _, key_file = self._get_key_path(key)
            try:
                os.remove(key_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise KvError(e.errno, "Can not delete entry %s" % (key_file))


class TomlKvStore(KvStore):
    """ Represents a TOML File Store """

    name = "toml"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        if not os.path.exists(self._store_path):
            with open(self._store_path, 'w+') as f:
                pass

    def load(self, **kwargs) -> KvPayload:
        """ Reads from the file """
        import toml
        with open(self._store_path, 'r') as f:
            try:
                data = toml.load(f, dict)
            except Exception as terr:
                raise KvError(errno.EINVAL, "Invalid TOML format %s",
                                   terr.__str__())
        recurse = True
        if 'recurse' in kwargs.keys():
            recurse = kwargs['recurse']
        return KvPayload(data, self._delim, recurse=recurse)

    def dump(self, data) -> None:
        """ Saves data onto the file """
        import toml
        with open(self._store_path, 'w') as f:
            toml.dump(data.get_data(), f)


class IniKvPayload(KvPayload):
    """ In memory representation of INI conf data """
    def __init__(self, config, delim='>'):
        super().__init__(config, delim)

    def _get_keys(self, keys: list, data, pkey: str = None,
        key_index: bool = True) -> None:
        for section in self._data.sections():
            for key in [option for option in self._data[section]]:
                keys.append(f"{section}{self._delim}{key}")

    def set(self, key, val):
        k = key.split(self._delim)
        if len(k) <= 1 or len(k) > 2:
            raise KvError(errno.EINVAL, "Invalid key %s for INI format", key)

        if k[0] not in self._data.sections():
            self._data.add_section(k[0])
        self._data.set(k[0], k[1], val)
        if key not in self._keys:
            self._keys.append(key)

    def get(self, key):
        k = key.split(self._delim)
        if len(k) <= 1 or len(k) > 2:
            raise KvError(errno.EINVAL, "Invalid key %s for INI format", key)
        try:
            return self._data.get(k[0],k[1])
        except (NoOptionError, NoSectionError):
            return None

    def delete(self, key, *args):
        k = key.split(self._delim)
        if len(k) <= 1 or len(k) > 2:
            raise KvError(errno.EINVAL, "Invalid key %s for INI format", key)

        if k[0] not in self._data.sections():
            return False

        is_deleted = False
        if len(k) == 2:
            is_deleted = self._data.remove_option(k[0], k[1])
            if is_deleted:
                if key in self._keys: self._keys.remove(key)

        if len(self._data.options(k[0])) == 0:
            is_deleted = self._data.remove_section(k[0])

        return is_deleted


class IniKvStore(KvStore):
    """ Represents a Ini File Store """

    name = "ini"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        self._config = ConfigParser()
        self._config.optionxform = lambda option: option

    def load(self, **kwargs) -> IniKvPayload:
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

    def load(self, **kwargs) -> KvPayload:
        """ Reads from the file """
        import json
        from json.decoder import JSONDecodeError

        recurse = True
        if 'recurse' in kwargs.keys():
            recurse = kwargs['recurse']

        try:
            self.data = json.loads(self._store_path)
        except JSONDecodeError as jerr:
            raise KvError(errno.EINVAL, "Invalid dict format %s", jerr.__str__())
        return KvPayload(self.data, self._delim, recurse=recurse)

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

    def load(self, **kwargs) -> KvPayload:
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
                raise KvError(errno.ENOENT, "Invalid properties store format "\
                    "%s. %s.", line, ex)
        return KvPayload(data, self._delim)

    def dump(self, data) -> None:
        """ Dump the data to desired file or to the source """
        kv_list = data.get_data()
        with open(self._store_path, 'w') as f:
            for key, val in kv_list.items():
                f.write("%s = %s\n" % (key, val))


class PillarStore(KvStore):
    """ Salt Pillar based KV Store """
    name = "salt"

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)

    def get(self, key):
        """Get pillar data for key."""
        import json
        cmd = f"salt-call pillar.get {key} --out=json"
        cmd_proc = SimpleProcess(cmd)
        out, err, rc = cmd_proc.run()

        if rc != 0:
            if rc == 127:
                err = f"salt command not found"
            raise KvError(rc, f"Cant get data for %s. %s.", key, err)

        res = None
        try:
            res = json.loads(out)
            res = res['local']

        except Exception as ex:
            raise KvError(errno.ENOENT, f"Cant get data for %s. %s.", key, ex)
        if res is None:
            raise KvError(errno.ENOENT, f"Cant get data for %s. %s."
                                        f"Key not present")
        return res

    def set(self, key, value):
        # TODO: Implement
        pass

    def delete(self, key):
        # TODO: Implement
        pass


class ConsulKvPayload(KvPayload):
    """ Backend adapter for consul api. """

    def __init__(self, consul: Consul, store_path: str = '', delim: str = '>'):
        if len(delim) > 1:
            raise KvError(errno.EINVAL, "Invalid delim %s", delim)
        self._delim = delim
        self._data = {}
        self._consul = consul
        self._store_path = store_path
        if self._store_path:
            if self._store_path.startswith('/'): self._store_path = self._store_path[1:]
            if not self._store_path.endswith('/'): self._store_path = self._store_path + '/'
        self._keys = self.get_keys()

    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def get(self, key: str, *args, **kwargs) -> str:
        """ Get value for consul key. """
        if not key in self._keys:
            return None
        index, data = self._consul.kv.get(self._store_path + key)
        if isinstance(data, dict):
            if data['Value'] is None:
                return ''
            return data['Value'].decode()
        elif data is None:
            return None
        else:
            raise KvError(errno.EINVAL, \
                "Invalid response from consul: %d:%s", index, data)

    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def _set(self, key: str, val: str, *args, **kwargs) -> Union[bool, None]:
        """ Set the value to the key in consul kv. """
        return self._consul.kv.put(self._store_path + key, str(val))


    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def _delete(self, key: str, data: dict, force: bool = False, *args, **kwargs) -> Union[bool, None]:
        """ Delete the key:value for the input key. """
        return self._consul.kv.delete(key = self._store_path + key, recurse = force)

    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def get_data(self, format_type: str = None, *args, **kwargs):
        """ Return a dict of kv pair. """
        self._data = {}
        from cortx.utils.schema import Format
        for kv in self._consul.kv.get('', recurse=True)[1]:
            self._data[kv['Key']] = kv['Value'].decode('utf-8') if kv['Value'] \
                is not None else ''
        if not format_type:
            return self._data
        return Format.dump(self._data, format_type)

    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def get_keys(self, starts_with: str = '', *args, **kwargs) -> list:
        """ Return a list of all the keys present. """
        keys=[]
        if starts_with:
            if not isinstance(starts_with, str):
                raise KvError(errno.EINVAL, "key should be a string, \
                    Invalid key: %s" % str(starts_with))
            else:
                key_list =  self._consul.kv.get(
                    self._store_path+starts_with, recurse=True, keys=True)[1]
        else:
            key_list =  self._consul.kv.get(self._store_path, keys=True)[1]
        if key_list:
            if self._store_path:
                for each_key in key_list:
                    keys.append(each_key.split(self._store_path)[1])
            else:
                keys.extend(key_list)
        return keys

    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def search(self, parent_key: str, search_key: str, search_val: str) -> list:
        """
        Searches the given dictionary for the key and value.
        Returns matching keys.
        """

        key_list=[]
        keys = self.get_keys(starts_with = parent_key)
        for key in keys:
            key_suffix = key.split(self._delim)[-1]
            if key_suffix == search_key:
                value = self.get(key) if parent_key else ''
                if value == search_val:
                    key_list.append(key)
        return key_list

class ConsulKVStore(KvStore):
    """ Consul basedKV store. """

    name = 'consul'

    def __init__(self, store_loc, store_path, delim='>'):
        KvStore.__init__(self, store_loc, store_path, delim)
        if store_loc:
            if ':' not in store_loc:
                store_loc = store_loc + ':8500'
        else:
            store_loc = '127.0.0.1:8500'
        host, port = store_loc.split(':')
        try:
            self.c = Consul(host=host, port=port)
            self._payload = ConsulKvPayload(self.c, self._store_path, self._delim)
        except Exception as e:
            raise KvError(errno.ECONNREFUSED, "Connection refused." \
                "Failed to eshtablish a new connection to consul endpoint: %s.\n %s", \
                store_loc, e)

    @ExponentialBackoff(exception=(ConsulException, HTTPError, RequestException), tries=4)
    def load(self, **kwargs) -> ConsulKvPayload:
        """ Return ConsulKvPayload object. """
        return self._payload

    def dump(self, data, *args, **kwargs):
        pass
