from cloudbench.env.entity import VirtualNetwork, VirtualMachine, Group

class EnvConfig(object):
    def __init__(self, f, cloud, env):
        self._env       = env
        self._groups    = {}
        self._vms       = {}
        self._vnets     = {}
        self._storages  = {}
        self._file      = f
        self._cloud     = cloud

        self.parse()

    def add_virtual_machine(self, vm_name, options):
        self._vms[vm_name] = \
                VirtualMachine(vm_name, options, self._env)

    def add_virtual_network(self, vnet_name, options):
        self._vnets[vnet_name] = \
                VirtualNetwork(vnet_name, options, self._env)

    def add_storage(self, storage_name, options):
        self._storages[storage_name] = \
                Storage(storage_name, options, self._env)

    def add_group(self, group_name, options):
        self._groups[group_name] = \
                Group(group_name, options, self._env)

    def virtual_machines(self):
        return self._vms

    def groups(self):
        return self._groups

    def virtual_networks(self):
        return self._vnets

    def storages(self):
        return self._storages

