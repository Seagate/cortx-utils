import os, errno, sys

class FileKvStorage:
    _type = dict

    def __init__(self, file_path):
        self._file_path = file_path

    def __str__(self):
        return str(self._file_path)

    def load(self):
        ''' Loads data from file of given format '''
        if not os.path.exists(self._file_path):
            return {}
        try:
            return self._load()
        except Exception as e:
            raise Exception('Unable to read file %s. %s' % (self._file_path, e))

    def dump(self, data):
        ''' Dump the anifest file to desired file or to the source '''
        dir_path = os.path.dirname(self._file_path)
        if len(dir_path) > 0 and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self._dump(data)