from src.utils.kv_store.file_storage.file_kv_storage import FileKvStorage

class JsonKvStorage(FileKvStorage):
    ''' Represents a JSON doc '''

    def __init__(self, file_path):
        Doc.__init__(self, file_path)

    def _load(self):
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def _dump(self, data):
        with open(self._file_path, 'w') as f:
            json.dump(data, f, indent=2)