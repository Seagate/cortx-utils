import yaml
from src.utils.conf_store.file_storage import FileStorage

class YamlStorage(FileStorage):

    def __init__(self, source):
        FileStorage.__init__(self, source)

    def _load(self):
        with open(self._source, 'r') as f:
            return yaml.safe_load(f)

    def _dump(self, data):
        with open(self._source, 'w') as f:
            yaml.dump(data, f)