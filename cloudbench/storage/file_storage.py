from .base_storage import BaseStorage

class FileStorage(BaseStorage):
    def __init__(self, env, fname):
        super(FileStorage, self).__init__(env)
        self._file = open(fname, 'a+')

    def read(self):
        pass

    def clear(self):
        pass

    def save(self, dic):
        pass

