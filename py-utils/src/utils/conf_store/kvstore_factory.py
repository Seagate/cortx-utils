import os
from src.utils.conf_store.storage import JsonStorage, YamlStorage

class KvStoreFactory:
    """
    Implements a KvStorage Factory.
    """
    def __init__(self, source):
        self._source = self.get_url(source)
        self._MAP = {"json": JsonStorage, "yaml": JsonStorage}
        self.__store = self.get_store_type()
    
    def get_url(self, source):
        try:
            if 'file://' in source:
                # Consider that supplied url as file type
                out = source.split('file://')
                return out[-1]
        except Exception as e:
            raise Exception(f"Invalid path given")

    def get_store_type(self):
        try:
            extension = os.path.splitext(self._source)[1][1:].strip().lower()
            store_obj = self._MAP[extension]
            return store_obj(self._source)
        except KeyError as error:
            raise KeyError(f"Unsupported file type:{error}")
        except Exception as e:
            raise Exception(f"Unable to read file {self._source}. {e}")

    def load(self):
        ''' Loads data from file of given format'''
        return self.__store.load()

    def dump(self, data):
        return self.__store.dump(data)
