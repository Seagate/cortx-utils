from src.utils.kv_store.file_storage.file_kv_storage import FileKvStorage

class Yaml(FileKvStorage):
    ''' Represents a YAML doc '''

    def __init__(self, file_path):
        Doc.__init__(self, file_path)

    def _load(self):
        with open(self._file_path, 'r') as f:
            return yaml.safe_load(f)

    def _dump(self, data):
        with open(self._file_path, 'w') as f:
            yaml.dump(data, f)