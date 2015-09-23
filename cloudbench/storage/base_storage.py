import ntplib
from time import ctime, time

import sys

class BaseStorage(object):
    def __init__(self, env):
        self._env    = env
        self._client = ntplib.NTPClient()
        self._delta  = None
        self.timestamp()

    def timestamp(self):
        try:
            if (self._delta is None):
                resp = self._client.request('0.pool.ntp.org').tx_timestamp
                self._delta = time() - float(resp)
        except Exception as e:
            print e
            # Just try again
            return self.timestamp()

        return str(int((time() - self._delta)*100)).zfill(14)

    def reverse_timestamp(self):
        return (sys.maxint - int(self.timestamp()))

    def save(self, dic):
        pass
