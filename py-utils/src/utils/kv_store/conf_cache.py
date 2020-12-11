class ConfCache:
    ''' implements a ConfCache in specified format. '''

    def __init__(self, doc):
        self._dirty = False
        self._doc = doc
        self.load()

    def load(self):
        if self._dirty:
            raise Exception('%s not synced to disk' % self._doc)
        self._data = self._doc.load()
        return self._data

    def dump(self):
        ''' Dump the anifest file to desired file or to the source '''
        self._doc.dump(self._data)
        self._dirty = False

    def _get(self, key, data):
        ''' Obtain value for the given key '''
        k = key.split('.', 1)
        if k[0] not in data.keys(): return None
        return self._get(k[1], data[k[0]]) if len(k) > 1 else data[k[0]]

    def get(self, key):
        if self._data is None:
            raise Exception('Configuration %s not initialized' % self._doc)
        return self._get(key, self._data)

    def _set(self, key, val, data):
        k = key.split('.', 1)
        if len(k) == 1:
            data[k[0]] = val
            return
        if k[0] not in data.keys() or type(data[k[0]]) != self._doc._type:
            data[k[0]] = {}
        self._set(k[1], val, data[k[0]])

    def set(self, key, val):
        ''' Sets the value into the DB for the given key '''
        self._set(key, val, self._data)
        self._dirty = True

    def convert(self, map, payload):
        """
        Converts 1 Schema to 2nd Schema depending on mapping dictionary.
        :param map: mapping dictionary :type:Dict
        :param payload: Payload Class Object with desired Source.
        :return: :type: Dict
        Mapping file example -
        key <input schema> : value <output schema>
        """
        for key in map.keys():
            val = self.get(key)
            payload.set(map[key], val)
        return payload