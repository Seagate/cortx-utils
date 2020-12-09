from src.utils.schema.payload import Payload

class ConfCache:

    def __init__(self):
       self._configuration_payload = {}
       self.payload = Payload

    def get(self, key): 
        # return self._configuration_payload[index].get(key) if self._configuration_payload[index].get(key) is not None else {}   
        key_sequence = "".join(str([e]) for e in key.split('.'))
        try:
            return eval(str(self._configuration_payload)+key_sequence)
        except KeyError:
            print('Given key/ combinations not found')
            
    def set(self, index, value):
        # self._configuration_payload[index] = self.payload.set(key, value)
        self._configuration_payload[index] = value
        return self._configuration_payload