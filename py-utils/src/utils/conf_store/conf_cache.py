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
            
    def load(self, index, value):
        # self._configuration_payload[index] = self.payload.set(key, value)
        self._configuration_payload[index] = value
        return self._configuration_payload
    
    def setter(self, index, keyList, valueList):
        try:
            push_value = {}
            for each_key in range(len(keyList)):
                push_value[keyList[each_key]] = valueList[each_key]
            self._configuration_payload[index].update(push_value)
        except TypeError as e:
            raise TypeError(f"Key should be a string: {e}")
        return self._configuration_payload[index]
    
    # def set(self, index, key, value):
    #     try:
    #         eval(self.get_Key_of_sequence(index,key)+'='+value)
    #     except:
    #         pass
    #     return self._configuration_payload
    
    # @staticmethod
    # def get_Key_of_sequence(index, key):
    #     key_sequence = "".join(str([e]) for e in key.split('.'))
    #     return (str(self._configuration_payload[index])+key_sequence)