class KvStorage:
    """
    This Abstract class will serve as base for key-value storage/db.
    The classes will extend this and provide their implementation of
    get, set and delete.
    """

    def __init__(self):
        pass

    def get(self, key):
        pass

    def set(self, key, value):
        pass

    def delete(self, key):
        pass
