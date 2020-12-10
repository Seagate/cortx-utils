import os
from src.utils.kv_store import KvStorage

class FileStorage(KvStorage):

    def __init__(self, source):
        super(FileStorage, self).__init__()
        self._source = source
    
    def load(self):
        if not os.path.exists(self._source):
            return {}
        try:
            return self._load()
        except Exception as e:
            raise Exception('Unable to read file %s. %s' % (self._source, e))
    
    def dump(self, data):
        dir_path = os.path.dirname(self._source)
        if len(dir_path) > 0 and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self._dump(data)
