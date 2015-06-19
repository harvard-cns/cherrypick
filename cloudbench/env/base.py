from cloudbench.env.config.xml_config import EnvXmlConfig
from cloudbench.env.clouds import AzureCloud
from cloudbench.storage import AzureStorage, FileStorage

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
        if obj is None:
            return None
        return self._uuid + self.benchmark_name() + str(obj).lower()


    def config(self):
        if self._config:
            return self._config
        if '.xml' in self._file:
            self._config = EnvXmlConfig(self._file, self._cloud, self)

        return self._config

    def manager(self):
        if self._manager:
            return self._manager

        if self._cloud == 'azure':
            self._manager = AzureCloud(self)

        return self._manager

    def storage(self):
        if isinstance(self._storage, str):
            if self._storage == 'azure':
                self._storage = AzureStorage(self)
            elif self._storage == 'file':
                self._storage = FileStorage(self)

        return self._storage

    def benchmark_name(self):
        return self._benchmark

    def cloud_name(self):
        return self._cloud

    def address_vm(self, vm):
        return self.manager().address_vm(vm)

    def stop_vm(self, vm):
        return self.manager().stop_vm(vm)

    def start_vm(self, vm):
        return self.manager().start_vm(vm)

    def delete_vm(self, vm):
        return self.manager().delete_vm(vm)

    def delete_vnet(self, vnet):
        return self.manager().delete_vnet(vnet)

    def delete_group(self, group):
        return self.manager().delete_group(group)

    def create_vm_endpoint(self, vm, endpoint):
        return self.manager().create_vm_endpoint(vm, endpoint)

    def create_vm(self, vm):
        return self.manager().create_vm(vm)

    def create_vnet(self, vnet):
        return self.manager().create_vnet(vnet)

    def create_group(self, group):
        return self.manager().create_group(group)

    def virtual_machines(self):
        return self.config().virtual_machines().values()

    def virtual_networks(self):
        return self.config().virtual_networks().values()

    def groups(self):
        return self.config().groups().values()

    def vm(self, name):
        vms = self.config().virtual_machines()
        if name in vms:
            return vms[name]
        return None

    def network(self, name):
        vns = self.config().virtual_networks()
        if name in vns:
            return vns[name]
        return None

    def group(self, name):
        groups = self.config().groups()
        if name in groups:
            return groups[name]
        return None


    def parallel(self, action, lst):
        threads = []
        for item in lst:
            th = threading.Thread(target=action, args=(item,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join()

    def setup(self):
        def create_vms(group):
            for vm in group.virtual_machines():
                vm.create()
        self.parallel(create_vms, self.groups())

    def teardown(self):
        def delete_vms(group):
            for vm in group.virtual_machines():
                vm.delete()

        self.parallel(delete_vms, self.groups())
        self.parallel(lambda vn: vn.delete(), self.virtual_networks())
        self.parallel(lambda gr: gr.delete(), self.groups())

    def start(self):
        # for vm in self.virtual_machines():
        #     vm.start()
        self.parallel(lambda vm: vm.start(True), self.virtual_machines())

    def stop(self):
        # for vm in self.virtual_machines():
        #     vm.stop()
        self.parallel(lambda vm: vm.stop(True), self.virtual_machines())
