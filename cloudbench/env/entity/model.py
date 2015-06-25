import inflection

from .entity_model import EntityModel, Entity
from .relation import *

from cloudbench import constants
from cloudbench.ssh import SSH

class VirtualMachine(EntityModel):
    location        = depends_on_one('Location')
    virtual_network = depends_on_one('VirtualNetwork')
    log_storages    = depends_on_many('LogStorage')
    security_groups = has_many('SecurityGroup')

    def __init__(self, *args, **kwargs):
        super(VirtualMachine, self).__init__(*args, **kwargs)
        self._ssh = None
        self._started = False

    def start(self):
        """ Ask the cloud factory for a boot up """
        self.factory.start_virtual_machine(self)
        self._started = True

    def stop(self):
        """ Ask the cloud factory for a shutdown """
        self.factory.stop_virtual_machine(self)
        self._started = False

    def reset(self):
        """ Ask the cloud factory for a reset """
        self.stop()
        self.start()

    def started(self):
        return self._started

    def stopped(self):
        return not self._started

    @property
    def username(self):
        """ Returns the username that is used to connect to this VM """
        if 'username' not in self._config:
            return constants.DEFAULT_VM_USERNAME

        return self._config['username']

    @property
    def url(self):
        """ Returns the URL to this vm """
        return self.factory.address_vm(self)

    def ssh(self, new=False):
        """ Return a SSH tunnel.

        If the new param is set, create a new SSH instance for every
        call to this function.
        """
        if new:
            return SSH(self, "".join([self.username, '@', self.url]))

        if self._ssh:
            return self._ssh

        self._ssh = SSH(self, "".join([self.username, '@', self.url]))
        return self._ssh

class VirtualNetwork(EntityModel):
    virtual_machines = has_many('VirtualMachine')

class Location(EntityModel):
    virtual_machines = has_many('VirtualMachine')
    log_storages     = has_many('LogStorages')

class SecurityGroup(EntityModel):
    virtual_machines = depends_on_many('VirtualMachine')
    location         = depends_on_one('Location')

class LogStorage(EntityModel):
    virtual_machines = has_many('VirtualMachine')
    location         = depends_on_one('Location')

__all__ = Entity.entities() + ['Entity']
