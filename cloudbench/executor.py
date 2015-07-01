class Executor(object):
    def __init__(self, env):
        self._env = env

    @property
    def env(self):
        return self._env

    def job(self, entities, function):
        """ Submit a job for execution """
        pass

    def run(self):
        pass

