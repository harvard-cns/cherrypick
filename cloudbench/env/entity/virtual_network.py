from cloudbench.env.entity import CloudEntity

class VirtualNetwork(CloudEntity):
    def __init__(self, name, config, env):
        super(VirtualNetwork,self).__init__(name, config, env)
        self._deleted = False

    def virtual_machines(self):
        ret = self._env.virtual_machines()
        return filter(lambda vm: vm.network() == self, ret)

    def group(self):
        groups = self._env.groups()

        config= self._config
        if ('group' not in config):
            return None

        group = config['group']

        res = filter(lambda g: g.name == group, groups)
        if res: return res[0]
        return None

    def address_range(self):
        return self._config['address-range']

    def location(self):
        if 'location' in self._config:
            return self._config['location']
        return None

    def create(self):
        if self._ready: return True

        if self.group() and (not self.group().ready_or_create()):
            return False

        if self._env.create_vnet(self):
            self._ready = True
            self._deleted = False

        return True

    def delete(self):
        if (not self._deleted) and self._env.delete_vnet(self):
            self._deleted = True
            self._ready = False
