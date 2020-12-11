from src.utils.kv_store.file_kv_storage import FileKvStorage
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

class JsonKvStorage(FileKvStorage):
    ''' Represents a JSON File Storage'''

    def __init__(self, file_path):
        FileKvStorage.__init__(self, file_path)

    def _load(self):
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def _dump(self, data):
        with open(self._file_path, 'w') as f:
            json.dump(data, f, indent=2)


class YamlKvStorage(FileKvStorage):
    ''' Represents a YAML File Storage '''

    def __init__(self, file_path):
        FileKvStorage.__init__(self, file_path)

    def _load(self):
        with open(self._file_path, 'r') as f:
            return yaml.safe_load(f)

    def _dump(self, data):
        with open(self._file_path, 'w') as f:
            yaml.dump(data, f)


class TomlKvStorage(FileKvStorage):
    ''' Represents a TOML File Storage '''

    def __init__(self, file_path):
        FileKvStorage.__init__(self, file_path)

    def _load(self):
        with open(self._file_path, 'r') as f:
            return toml.load(f, dict)

    def _dump(self, data):
        with open(self._file_path, 'w') as f:
            toml.dump(data, f)


class IniKvStorage(FileKvStorage):
    ''' Represents a YAML File Storage '''

    def __init__(self, file_path):
        self._config = configparser.ConfigParser()
        FileKvStorage.__init__(self, file_path)
        self._type = configparser.SectionProxy

    def _load(self):
        self._config.read(self._file_path)
        return self._config

    def _dump(self, data):
        with open(self._file_path, 'w') as f:
            data.write(f)

class DictKvStorage(FileKvStorage):
    '''Represents Dictionary Without file'''

    def __init__(self, data={}):
        FileKvStorage.__init__(self, data)

    def load(self):
        return self._file_path

    def dump(self, data):
        self._file_path = data

class JsonMessageKvStorage(Json):
    def __init__(self, json_str):
        """
        Represents the Json Without FIle
        :param json_str: Json String to be processed :type: str
        """
        Json.__init__(self, json_str)

    def load(self):
        """
        Load the json to python interpretable Dictionary Object
        :return: :type: Dict
        """
        return json.loads(self._file_path)

    def dump(self, data: dict):
        """
        Set's the data _source after converting to json
        :param data: :type: Dict
        :return:
        """
        self._file_path = json.dumps(data)

class TextKvStorage(FileKvStorage):

    '''Represents a TEXT File Storage'''
    def __init__(self, file_path):
        FileKvStorage.__init__(self, file_path)

    def _load(self):
        '''Loads data from text file'''
        with open(self._file_path, 'r') as f:
            return f.read()

    def _dump(self, data):
        '''Dump the data to desired file or to the source'''
        with open(self._file_path, 'w') as f:
            f.write(data)