from src.utils.schema.payload import Payload

class ConfCache:

    def __init__(self):
       self._configuration_payload = {}
       # need to be discussed
       self.payload = Payload

    def get(self, index, key=None, default_value = None):

        try:
            if index in self._configuration_payload:
                if key is not None:
                    key_sequence = "".join(str([e]) for e in key.split('.'))
                    return eval(str(self._configuration_payload[index])+key_sequence)
                else:
                    return self._configuration_payload[index]
        except KeyError:
            print('Value for given key index not found')
            return default_value
            
    def set(self, index, value):
        # self._configuration_payload[index] = self.payload.set(key, value)
        self._configuration_payload[index] = value
        return self._configuration_payload