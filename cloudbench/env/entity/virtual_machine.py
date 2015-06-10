from cloudbench.env.entity import CloudEntity
from cloudbench.ssh import SSH

from cloudbench import constants

class VirtualMachineEndpoint(CloudEntity):
    def __init__(self, name, config, env):
        super(VirtualMachineEndpoint,self).__init__(name, config, env)

class VirtualMachine(CloudEntity):
    def __init__(self, name, config, env):
        super(VirtualMachine,self).__init__(name, config, env)
        self._ssh = None
        self._deleted = False
        self._endpoints = []

        if 'endpoints' in config:
            for ep in config['endpoints']:
                self.add_endpoint(
                    ep['name'], ep['protocol'],
                    ep['public-port'], ep['private-port'])


    def group(self):
        groups = self._env.groups()

        config= self._config
        if ('group' not in config):
            return None

        group = config['group']

        res = filter(lambda g: g.name == group, groups)
        if res: return res[0]
        return None

    def network(self):
        vnets = self._env.virtual_networks()

        config= self._config
        if ('virtual-network' not in config):
            return None

        vnet = config['virtual-network']

        res = filter(lambda vn: vn.name == vnet, vnets)
        if res: return res[0]
        return None

    def endpoints(self):
        return self._endpoints

    def add_endpoint(self, name=None, protocol=None, pub_port=None,
            pri_port=None):
        ep = name
        if isinstance(ep, str):
            ep = VirtualMachineEndpoint( name, {'name': name,
                'protocol': protocol, 'public_port': pub_port,
                'private_port': pri_port}, self._env)
        self._endpoints.append(ep)
        return ep

    def create_endpoint(self, name, protocol=None, pub_port=None,
            pri_port=None):
        ep = name
        if isinstance(ep, str):
            ep = self.add_endpoint(name, protocol, pub_port, pri_port)
        self._env.create_vm_endpoint(self, ep)

    def create(self):
        if self._ready: return True

        if self.group() and (not self.group().ready_or_create()):
            return False

        if self.network() and (not self.network().ready_or_create()):
            return False

        if self._env.create_vm(self):
            self._ready = True
            self._deleted = False

        return self._ready

    def delete(self):
        if (not self._deleted) and self._env.delete_vm(self):
            self._deleted = True
            self._ready = False


    def username(self):
        if 'username' not in self._config:
            return constants.DEFAULT_VM_USERNAME

        return self._config['username']


    def ssh(self):
        if self._ssh:
            return self._ssh

        self._ssh = SSH("".join([self.username(), '@',
            self._env.address_vm(self)]))

        return self._ssh

