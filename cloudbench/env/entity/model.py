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

    @property
    def storage_type(self):
        if self.storage:
            return self.storage.split('-')[0]
        return None

    @property
    def storage_count(self):
        if self.storage:
            return int(self.storage.split('-')[1])
        return None

    @property
    def storage_size(self):
        if self.storage:
            return int(self.storage.split('-')[2])
        return None

    @property
    def storage(self):
        if 'storage' in self.config:
            return self.config['storage']

        at_least_one_config = False
        storage_type = 'gp2'
        if 'storage-type' in self.config:
            storage_type = self.config['storage-type']
            at_least_one_config = True

        storage_count = '1'
        if 'storage-count' in self.config:
            storage_count = self.config['storage-count']
            at_least_one_config = True

        storage_size = '100'
        if 'storage-size' in self.config:
            storage_size = self.config['storage-size']
            at_least_one_config = True

        if at_least_one_config:
            return '%s-%s-%s' % (storage_type, storage_count, storage_size)

        return None

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
