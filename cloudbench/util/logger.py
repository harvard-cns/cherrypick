import sys

class OutputStream(type):
    def __lshift__(self, other):
        return self.get() << other

class Logger(object):
    __metaclass__ = OutputStream
    _singleton = None

    def write(self, string):
        pass

    def __lshift__(self, obj):
        self.write(str(obj))
        return self

    @classmethod
    def get(cls):
        if not cls._singleton:
            cls._singleton = cls()
        return cls._singleton


class Debug(Logger):
    _singleton = None
    _verbosity = 0

    def __init__(self, verbosity):
        self._verbosity = verbosity

    def write(self, string):
        if Debug._verbosity >= self._verbosity:
            sys.stderr.write(string)

    @classmethod
    def verbosity(cls, level):
        cls._verbosity = level


Debug.info = Debug(3)
Debug.warn = Debug(2)
Debug.err = Debug(1)
Debug.cmd = Debug(0)


__all__ = ['Debug']
