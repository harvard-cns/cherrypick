""" A Json storage to keep benchmark specific values """

from base_storage import BaseStorage

import json

class JsonStorage(BaseStorage):
    def __init__(self, env, fname):
        self._file = open(fname, 'a+')
        self._obj = self.read()

        super(JsonStorage, self).__init__(env)

    def read(self):
        """ Read the dumped json object """
        self._file.seek(0)
        try:
            return json.load(self._file)
        except ValueError:
            return {}


    def clear(self):
        """ Remove all the saved data """
        self._file.truncate(0)

    def save(self, dic):
        """ Save all the data into the file """
        self.clear()
        json.dump(dic, self._file)
        self._obj = dic
        return self

    def __setitem__(self, name, value):
        self._obj[name] = value
        self.save(self._obj)
        return value

    def __getitem__(self, name):
        if name in self._obj:
            return self._obj[name]
        return None

    def __delitem__(self, name):
        del self._obj[name]
        self.save(self._obj)
