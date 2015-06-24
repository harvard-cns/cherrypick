from cloudbench.env.entity import CloudEntity

class VirtualNetwork(CloudEntity):
    def __init__(self, name, config, env):
        super(VirtualNetwork, self).__init__(name, config, env)
        self._deleted = False

    def virtual_machines(self):
        """ Returns the list of virtual machines attached to this
        network """
        vms = self._env.virtual_machines()
        return [vm for vm in vms if vm.network() == self]

    def address_range(self):
        """ Returns the address range for this virtual network """
        return self._config['address-range']

    def location(self):
        """ Returns the location of this virtual network """
        if 'location' in self._config:
            return self._config['location']
        return None

    def create(self):
        """ Create this virtual network """
        if self._ready:
            return True

        if self._env.create_vnet(self):
            self._ready = True
            self._deleted = False

        return True

    def delete(self):
        if (not self._deleted) and self._env.delete_vnet(self):
            self._deleted = True
            self._ready = False
