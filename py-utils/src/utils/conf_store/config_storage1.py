
from src.utils.kvstore.kvstore  import KvStore
from src.utils.config_store.conf_cache import ConfCache
from src.utils.config_store.config_type import ConfigType

# ConfigStore -> confType and Configuration

# open the file -> reads config and setup the filehandle

# filehandle


class ConfingStore:

    def __init__(self, confType):
        '''
        confType - type of the configuration : string
        '''
        self.confType = ConfigType(confType)
        self._store = KvStore
        # for testing
        self.configuration_payload = {}
    
    '''
    index - handle <file handle>
    /etc/cortx/sspl.conf
    '''
    def load(self, index, store, force=False):
        self._store = store

        if index in self.configuration_payload.keys():
            if force == False:
                pass
                # do raise index already present exception
            self.configuration_payload[index] = self._store.get(key)
        return self.configuration_payload
        
    def get(self, index, key):
        return self.configuration_payload[index][key]

    def set(self, index, key, value):
        pass

    def save(self):
        pass
    def copy(self, index1, index2):
        pass
    def Merge(self, index1, index2):
        pass
