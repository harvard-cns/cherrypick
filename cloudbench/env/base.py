from cloudbench.env.config.xml_config import EnvXmlConfig
from cloudbench.env.clouds import AzureCloud, AwsCloud
from cloudbench.storage import AzureStorage, FileStorage
from cloudbench.util import parallel

import threading
import time

class Env(object):
    def __init__(self, cloud, f, benchmark, storage):
        self._cloud = cloud
        self._file = f
        self._config = None
        self._manager = None
        self._storage = storage
        self._benchmark = benchmark
        self._uuid = 'cb'

    def namify(self, obj):
        """ Normalize the name of objects based on the benchmark and the
        actual object name """
        if obj is None:
            return None
        return self._uuid + self.benchmark_name() + str(obj).lower()


    def config(self):
        """ Return the configuration """
        if self._config:
            return self._config
        if '.xml' in self._file:
            self._config = EnvXmlConfig(self._file, self._cloud, self)
            self._config.parse()

        return self._config

    def manager(self):
        """ Return the manager """
        if self._manager:
            return self._manager

        if self._cloud == 'azure':
            self._manager = AzureCloud(self)
        elif self._cloud == 'aws':
            self._manager = AwsCloud(self)

        return self._manager

    def storage(self):
        """ Return the storage where we save the resulting data """
        if isinstance(self._storage, str):
            if self._storage == 'azure':
                self._storage = AzureStorage(self)
            elif self._storage == 'file':
                self._storage = FileStorage(self)

        return self._storage

    def benchmark_name(self):
        """ Returns the name of the active benchmark """
        return self._benchmark

    def cloud_name(self):
        """ Returns the name of the cloud provider """
        return self._cloud

    def vm(self, name):
        """ Shorthand to find a virtual-machine """
        return self.virtual_machines()[name]

    # Delegate these calls to the manager, maybe he knows what to do
    # with them?
    def __getattr__(self, name):
        """ Delegates methods that are not defined to the manager """

        if name.startswith('create') or name.startswith('delete'):
            if hasattr(self.manager(), name):
                return getattr(self.manager(), name)

            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, name))

        return getattr(self.config(), name)

    # def address_vm(self, vm):
    #     return self.manager().address_vm(vm)

    # def stop_vm(self, vm):
    #     return self.manager().stop_vm(vm)

    # def start_vm(self, vm):
    #     return self.manager().start_vm(vm)

    # def delete_vm(self, vm):
    #     return self.manager().delete_vm(vm)

    # def delete_vnet(self, vnet):
    #     return self.manager().delete_vnet(vnet)

    # def delete_group(self, group):
    #     return self.manager().delete_group(group)

    # def create_vm_endpoint(self, vm, endpoint):
    #     return self.manager().create_vm_endpoint(vm, endpoint)

    # def create_vm(self, vm):
    #     return self.manager().create_vm(vm)

    # def create_vnet(self, vnet):
    #     return self.manager().create_vnet(vnet)

    # def create_group(self, group):
    #     return self.manager().create_group(group)

    def setup(self):
        """ Setup the VMs """
        def satisfied(ent):
            """ Returns true if the requirement of an entity are
            satisfied """
            for dep in ent.dependencies:
                deps = getattr(ent, dep)()
                if not deps:
                    continue
                
                if not isinstance(deps, list):
                    deps = [deps]

                # if any of the dependencies are not satisfied, return
                # False
                if any(map(lambda x: not x.created(), deps)):
                    return False

            return True

        # Collect everything
        everything = set()
        for ent in self.entities().values():
            everything = everything.union(set(ent.values()))

        while everything:
            to_remove = set()
            to_create = set()
            for ent in everything:
                if satisfied(ent) and not ent.created():
                    to_create.add(ent)

            parallel(lambda x: x.create(), to_create)
            to_remove = set(filter(lambda x: x.created(), to_create))
            everything = everything - to_remove

    def teardown(self):
        """ Delete everything """
        def satisfied(ent):
            """ Returns true if the requirement of an entity are
            satisfied """
            for dep in ent.dependents:
                deps = getattr(ent, dep)()
                if not deps:
                    continue
                
                if not isinstance(deps, list):
                    deps = [deps]

                # if any of the dependencies are not satisfied, return
                # False
                if any(map(lambda x: not x.deleted(), deps)):
                    return False

            return True

        # Collect everything
        everything = set()
        for ent in self.entities().values():
            everything = everything.union(set(ent.values()))

        while everything:
            to_remove = set()
            to_delete = set()
            for ent in everything:
                if satisfied(ent) and not ent.deleted():
                    to_delete.add(ent)

            parallel(lambda x: x.delete(), to_delete)
            to_remove = set(filter(lambda x: x.deleted(), to_delete))
            everything = everything - to_remove

    def start(self):
        """ Start the VMs in parallel """
        parallel(lambda vm: vm.start(True), self.virtual_machines())

    def stop(self):
        """ Stop the VMs in parallel """
        parallel(lambda vm: vm.stop(True), self.virtual_machines())
