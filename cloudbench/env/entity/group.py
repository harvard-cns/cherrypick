from cloudbench.env.entity import CloudEntity

class Group(CloudEntity):
    def __init__(self, name, config, env):
        super(Group,self).__init__(name, config, env)
        self._deleted = False

    def virtual_machines(self):
        ret = self._env.virtual_machines()
        return filter(lambda vm: vm.group() == self, ret)

    def virtual_networks(self):
        ret = self._env.virtual_networks()
        return filter(lambda vm: vm.group() == self, ret)

    def create(self):
        if self._ready: return True

        if self._env.create_group(self):
            self._ready = True
            self._deleted = False

        return True

    def location(self):
        if 'location' in self._config:
            return self._config['location']
        return None

    def delete(self):
        if (not self._deleted) and self._env.delete_group(self):
            self._deleted = True
            self._ready = False

