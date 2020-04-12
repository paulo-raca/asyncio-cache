from time import time

class Serializer():
    """
    Abstraction for data serialization / deserialization
    """

    def encode(self, value):
        """
        Encode the value into a blob (bytes)
        """
        raise NotImplemented()

    def decode(self, encoded):
        """
        Decode the value from a blob
        """
        raise NotImplemented()

class JsonSerializer():
    def __init__(self, **kwargs):
        self.encode_args  = kwargs

    """
    Serializes data as JSON strings
    """
    def encode(self, value):
        import json
        return json.dumps(value, **self.encode_args ).encode('utf-8')

    def decode(self, encoded):
        import json
        return json.loads(encoded.decode('utf-8'))

class PickleSerializer():
    def __init__(self, **kwargs):
        self.encode_args = kwargs

    """
    Serializes data as JSON strings
    """
    def encode(self, value):
        import pickle
        return pickle.dumps(value, **self.encode_args )

    def decode(self, encoded):
        import pickle
        return pickle.loads(encoded)
