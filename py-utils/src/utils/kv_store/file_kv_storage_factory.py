#!/bin/python3
import os
from src.utils.kv_store.kv_storage_collections import JsonKvStorage, YamlKvStorage, TomlKvStorage


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

class FileKvStorageFactory:
    name = "file"
    """
    Implements a common file_storage to represent Json, Toml, Yaml, Ini Doc.
    """

    def __init__(self, file_path):
        self._file_path = file_path
        # Mapping of file extensions and doc classes.
        self._MAP = {
            "json": JsonKvStorage, "yaml": YamlKvStorage, "toml": TomlKvStorage
        }
        self._kvstore = self.get_store_type()

    def id(self):
        return 'file'

    def get_store_type(self):
        """
        Get mapped doc class object bases on file extension
        """
        try:
            extension = os.path.splitext(self._file_path)[1][1:].strip().lower()
            """
            The below if statement is just for temporary purpose to handle
            serial number fie that has no extension to it.
            In future the file will be moved to JSON with key, value pair and
            the below check will be removed.
            """
            if not extension:
                extension = "txt"
            store_obj = self._MAP[extension]
            return store_obj(self._file_path)
        except KeyError as error:
            raise KeyError(f"Unsupported file type:{error}")
        except Exception as e:
            raise Exception(f"Unable to read file {self._file_path}. {e}")

    def load(self):
        """ Loads data from file of given format"""
        return self._kvstore._load()

    def dump(self, data):
        """ Dump the data to desired file or to the source """
        self._kvstore._dump(data)
