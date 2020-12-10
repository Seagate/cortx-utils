import json
from src.utils.conf_store.file_storage import FileStorage

class JsonStorage(FileStorage):
    def __init__(self, path):
        # load config from path provided
        FileStorage.__init__(self, path)
    
    def _load(self):
        with open(self._source, 'r') as f:
            return json.load(f)

    def _dump(self, data):
        with open(self._source, 'w') as f:
            json.dump(data, f, indent=2)
