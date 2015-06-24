from cloudbench.env.entity import CloudEntity
from cloudbench.ssh import SSH

from cloudbench import constants
from cloudbench.util import entity_repr

import time, random

class VirtualMachine(CloudEntity):
    """ Representation of a (linux) virtual machine in the cloud.  It is
    possible to use the ssh() method to access the VM, and execute commands
    remotely.
    """
    def __init__(self, name, config, env):
        super(VirtualMachine, self).__init__(name, config, env)
        self._ssh = None
        self._deleted = False

    def _find_entity_in_array(self, name, array):
        """ Finds an entity in an array and returns the first instance
        """
        config = self._config
        if name not in config:
            return None

        entity = config[name]
        return next(item for item in array if item.name == entity)

    def security_group(self):
        """ Return the security group where this VM is a part of """
        return self._find_entity_in_array('security-group',
                                          self._env.security_groups())

    def network(self):
        """ Return the network for this VM """
        return self._find_entity_in_array('virtual-network',
                                          self._env.virtual_networks())

    def create(self):
        """ Create the VM """
        if self._ready:
            return True

        if self._env.create_vm(self):
            self._ready = True
            self._deleted = False

        return self._ready

    def delete(self):
        """ Delete the VM """
        if (not self._deleted) and self._env.delete_vm(self):
            self._deleted = True
            self._ready = False

    def start(self, retry=False):
        """ Start the VM """
        ret = self._env.start_vm(self)
        while (ret == False) and retry:
            time.sleep(random.uniform(5, 50)+60)
            ret = self._env.start_vm(self)

    def stop(self, retry=False):
        """ Stop(deallocate) the VM

        Mainly to save money :-)
        """
        ret = self._env.stop_vm(self)
        while (ret == False) and retry:
            time.sleep(random.uniform(5, 50)+60)
            ret = self._env.stop_vm(self)

    def username(self):
        """ Returns the username that is used to connect to this VM """
        if 'username' not in self._config:
            return constants.DEFAULT_VM_USERNAME

        return self._config['username']

    def url(self):
        """ Returns the URL to this vm """
        return self._env.address_vm(self)

    def ssh(self, new=False):
        """ Return a SSH tunnel.

        If the new param is set, create a new SSH instance for every
        call to this function.
        """
        if new:
            return SSH("".join([self.username(), '@', self.url()]))

        if self._ssh:
            return self._ssh

        self._ssh = SSH("".join([self.username(), '@', self.url()]))
        return self._ssh

