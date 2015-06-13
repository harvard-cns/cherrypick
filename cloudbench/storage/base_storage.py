import ntplib
from time import ctime

class BaseStorage(object):
    def __init__(self, env):
        self._env    = env
        self._client = ntplib.NTPClient()

    def timestamp(self):
        resp = self._client.request('pool.ntp.org')
        return str(int(resp.tx_timestamp * 100)).zfill(14)

    def save(self, env):
        pass
