import sys

class Logger(object):
    def write(self, string):
        pass

    def __lshift__(self, obj):
        self.write(str(obj))
        return self


class Debug(Logger):
    def write(self, string):
        sys.stderr.write(string)

    def get(self):
        if Debug._singleton


__all__ = ['err']
