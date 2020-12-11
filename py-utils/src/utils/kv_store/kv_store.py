
from src.utils.kv_store.kv_storage import KvStorage

class KvStore:
    """
    This class will take KvStorage implementation as input and be front facing
    to the consumer.
    """

    def __init__(self, kvStorage):
        self._storage = kvStorage

    def get(self, key):
        return self._storage.get(key)

    def set(self, key, value):
        return self._storage.set(key, value)

    def delete(self, key):
        return self._storage.delete(key)