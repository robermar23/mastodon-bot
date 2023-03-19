import pickle
from datetime import datetime, timedelta
from collections import UserDict


class timed_dict(UserDict):
    def __init__(self, max_age_hours=1, *args, **kwargs):
        self.max_age_hours = max_age_hours
        self.timestamp_dict = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.data[key] = value
        self.timestamp_dict[key] = datetime.now()

    def __delitem__(self, key):
        del self.data[key]
        del self.timestamp_dict[key]

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.data)
    
    def copy(self):
        new_dict = timed_dict(max_age_hours=self.max_age_hours)
        new_dict.data = self.data.copy()
        new_dict.timestamp_dict = self.timestamp_dict.copy()
        return new_dict
    
    def __getstate__(self):
        return (self.max_age_hours, self.data, self.timestamp_dict)
    
    def __setstate__(self, state):
        self.max_age_hours, self.data, self.timestamp_dict = state
        
    def serialize(self):
        return pickle.dumps(self)
        
    def remove_old_items(self):
        now = datetime.now()
        for key, timestamp in self.timestamp_dict.copy().items():
            age = now - timestamp
            if age > timedelta(hours=self.max_age_hours):
                del self[key]
    
    @staticmethod
    def deserialize(data):
        return pickle.loads(data)
