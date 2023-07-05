import pickle
import json
from collections import UserDict
from redis import Redis


class redis_timed_dict(UserDict):
    def __init__(self, redis_connection, key, max_age_hours=24):
        super().__init__()

        self.max_age_hours = max_age_hours

        if not redis_connection:
            raise Exception("redis_connection not provided")

        # redis_password, redis_host, redis_port, redis_db = self.parse_redis_connection_string(redis_connection)
        # self.cache = Redis(host=redis_host, db=redis_db, port=redis_port, password=redis_password)
        self.redis_client = Redis.from_url(redis_connection)

        self.key = key
        self.max_age_hours = max_age_hours

    def _decode_value(self, value):
        try:
            decoded_value = value.decode('utf-8')
            if decoded_value.startswith('[') and decoded_value.endswith(']'):
                return json.loads(decoded_value)
            return decoded_value
        except AttributeError:
            return value

    def __getitem__(self, key):
        value = self.redis_client.hget(self.key, key)
        if value is None:
            raise KeyError(key)
        return self._decode_value(value)

    def __setitem__(self, key, value):
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        else:
            value = str(value)
        self.redis_client.hset(self.key, key, value)
        if self.max_age_hours > 0:
            self.redis_client.expire(self.key, self.max_age_hours * 60 * 60)

    def __delitem__(self, key):
        result = self.redis_client.hdel(self.key, key)
        if result == 0:
            raise KeyError(key)

    def __contains__(self, key):
        return self.redis_client.hexists(self.key, key)

    def __iter__(self):
        return iter(self.redis_client.hkey(self.key))

    def __len__(self):
        return self.redis_client.hlen(self.key)

    def keys(self):
        return self.redis_client.hkeys(self.key)

    def values(self):
        result = self.redis_client.hvals(self.key)
        return [value.decode() for value in result]

    def items(self):
        result = self.redis_client.hgetall(self.key)
        return [
            (key.decode('utf-8'), self._decode_value(value))
            for key, value in result.items()
        ]

    # def copy(self):
    #     new_dict = redis_timed_dict(max_age_hours=self.max_age_hours)
    #     new_dict.data = self.data.copy()
    #     return new_dict

    def serialize(self):
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        return pickle.loads(data)
