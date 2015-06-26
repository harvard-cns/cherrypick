import ntplib
from time import ctime, time

class BaseStorage(object):
    def __init__(self, env):
        self._env    = env
        self._client = ntplib.NTPClient()
        self._delta  = None
        self.timestamp()

    def timestamp(self):
        if (self._delta is None):
            resp = self._client.request('pool.ntp.org').tx_timestamp
            self._delta = time() - float(resp)

        return str(int((time() - self._delta)*100)).zfill(14)

    def save(self, dic):
        pass
