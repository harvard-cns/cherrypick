from cloudbench.util import entity_repr

class CloudEntity(object):
    def __init__(self, name, config, env):
        self._env    = env
        self._name   = name
        self._config = config
        self._ready  = False

    def create(self):
        self._ready = True
        return True

    def ready_or_create(self):
        if (self._ready):
            return True
        return self.create()

    def extend(self, attrs):
        self._config.update(attrs)

    def delete(self):
        self._ready = False

    def config(self):
        return self._config

    def __getattr__(self, name):
        name = name.replace('_', '-')
        if name in self._config:
            return self._config[name]

        raise Exception("%s is not specified." % name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return entity_repr(self, self.__class__.__name__)

