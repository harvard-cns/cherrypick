import inflection

from .entity_model import EntityModel, Entity
from .relation import *
from .behavior import *
from .linux import Ubuntu

from cloudbench import constants

from threading import RLock

class VirtualMachine(Preemptable, EntityModel, Ubuntu):
    location = depends_on_one('Location')
    virtual_network = depends_on_one('VirtualNetwork')
    log_storages = depends_on_many('LogStorage')
    security_groups = has_many('SecurityGroup')

    @property
    def username(self):
        """ Returns the username that is used to connect to this VM """
        if 'username' not in self._config:
            return constants.DEFAULT_VM_USERNAME

        return self._config['username']

    @property
    def url(self):
        """ Returns the URL to this vm """
        return self.factory.address_virtual_machine(self)

class VirtualNetwork(EntityModel):
    virtual_machines = has_many('VirtualMachine')
    location         = depends_on_one('Location')

class Location(EntityModel):
    virtual_machines = has_many('VirtualMachine')
    log_storages     = has_many('LogStorages')
    virtual_networks = has_many('VirtualNetwork')

class SecurityGroup(EntityModel):
    virtual_machines = depends_on_many('VirtualMachine')

class LogStorage(EntityModel):
    virtual_machines = has_many('VirtualMachine')
    location         = depends_on_one('Location')

__all__ = Entity.entities() + ['Entity']
