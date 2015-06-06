class Env(object):
    def config(self):
        pass

    def __init__(self, cloud, f):
        self._cloud = cloud
        self._file  = f
        self._config = None
        self._manager = None


    def config(self):
        if self._config: return self._config
        if '.xml' in self._file:
            self._config = EnvXmlConfig(self._file, self._cloud, self)

        return self._config

    def manager(self):
        if self._manager: return self._manager

        if self._cloud == 'azure':
            self._manager = AzureManager()

        return self._manager


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

    def setup(self):
        for vm in self.virtual_machines(): vm.create()

    def teardown(self):
        for vm in self.virtual_machines(): vm.delete()
        for vnet in self.virtual_networks(): vnet.delete()
        for group in self.groups(): group.delete()

class CloudObject(object):
    def __init__(self, name, config, env):
        self._env    = env
        self._name   = name
        self._config = config
        self._ready  = False

    def create(self):
        self._ready = True
        return True

    def ready_or_create(self):
        if (self._ready):
            return True
        return self.create()

    def delete(self):
        self._ready = False

    def __getattr__(self, name):
        if name in self._config:
            return self._config[name]

        raise Exception("%s is not specified." % name)

    def __str__(self):
        return self.name

class Storage(CloudObject):
    def __init__(self, name, config, env):
        super(Storage,self).__init__(name, config, env)

class VirtualMachine(CloudObject):
    def __init__(self, name, config, env):
        super(VirtualMachine,self).__init__(name, config, env)

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

    def create(self):
        if self._ready: return True

        if self.group() and (not self.group().ready_or_create()):
            return False

        if self.network() and (not self.network().ready_or_create()):
            return False

        if env.create_vm(self):
            self._ready = True

        return self._ready

    def delete(self):
        env.delete_vm(self)
        self._ready = False


class VirtualNetwork(CloudObject):
    def __init__(self, name, config, env):
        super(VirtualNetwork,self).__init__(name, config, env)

    def virtual_machines(self):
        ret = self._env.virtual_machines().values()
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

        if env.create_vnet(self):
            self._ready = True

        return True

    def delete(self):
        env.delete_vnet(self)
        self._ready = False


class Group(CloudObject):
    def __init__(self, name, config, env):
        super(Group,self).__init__(name, config, env)

    def virtual_machines(self):
        ret = self._env.virtual_machines().values()
        return filter(lambda vm: vm.group() == self, ret)

    def virtual_networks(self):
        ret = self._env.virtual_networks().values()
        return filter(lambda vm: vm.group() == self, ret)

    def create(self):
        if self._ready: return True

        if env.create_group(self):
            self._ready = True

        return True

    def location(self):
        if 'location' in self._config:
            return self._config['location']
        return None

    def delete(self):
        env.delete_group(self)
        self._ready = False

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

import xml.etree.ElementTree as ET
class EnvXmlConfig(EnvConfig):
    def __init__(self, f, cloud, env):
        super(EnvXmlConfig,self).__init__(f, cloud, env)


    def parse(self):
        self._tree = root = ET.parse(self._file)
        cloud = root.find(self._cloud)

        def parse_vms(this, cloud):
            for vm in cloud.findall('./virtual-machines/virtual-machine'):
                atts = vm.attrib
                this.add_virtual_machine(atts['name'], atts)

        def parse_groups(this, cloud):
            for gr in cloud.findall('./groups/group'):
                atts = gr.attrib
                this.add_group(atts['name'], atts)

        def parse_vnets(this, cloud):
            for vn in cloud.findall('./virtual-networks/virtual-network'):
                atts = vn.attrib
                this.add_virtual_network(atts['name'], atts)

        def parse_storages(this, cloud):
            for st in cloud.findall('./storages/storage'):
                atts = st.attrib
                this.add_virtual_network(atts['name'], atts)
        
        parse_groups(self, cloud)
        parse_vnets(self, cloud)
        parse_vms(self, cloud)
        parse_storages(self, cloud)


import subprocess
import uuid
import base64

class AzureManager(object):
    def __init__(self):
        self._uuid = 'deadbeef' #str(uuid.uuid4())

    def uuid(self, obj):
        if obj is None: return None
        return self._uuid + '' + str(obj)

    def execute(self, command):
        p = subprocess.Popen(command)
        return (p.wait() == 0)

    def if_available(self, option, value):
        if value:
            return [option, str(value)]
        return []

    def create_vm(self, vm):
        cmd  = ['azure', 'vm', 'create', '-z', vm.type]
        cmd += self.if_available('-a', self.uuid(vm.group()))
        cmd += self.if_available('-w', self.uuid(vm.network()))
        cmd += ['-e', '22', self.uuid(vm.name), vm.image,  'omid', 'q12345^Y']

        print "----------------------------------------"
        print "Creating vm: %s" % vm.name
        print "Executing %s" % " ".join(cmd)

        return self.execute(cmd)

    def delete_vm(self, vm):
        cmd = ['azure', 'vm', 'delete', self.uuid(vm.name)]
        if not self.execute(cmd): return False
        cmd = ['azure', 'service', 'delete', self.uuid(vm.name)]
        if not self.execute(cmd): return False
        cmd = ['azure', 'storage', 'delete', self.uuid(vm.name)]
        if not self.execute(cmd): return False

        return True

    def create_vnet(self, vnet):
        cmd  = ['azure', 'network', 'vnet', 'create']
        cmd += self.if_available('-e', vnet.address_range())
        cmd += self.if_available('-l', vnet.location())
        cmd += self.if_available('-a', self.uuid(vnet.group()))
        cmd += [self.uuid(vnet.name)]

        print "----------------------------------------"
        print "Creating vnet: %s" % vnet.name
        print "Executing %s" % " ".join(cmd)

        return self.execute(cmd)

    def delete_vnet(self, vnet):
        for vm in vnet.virtual_machines(): self.delete_vm(vm)

        cmd  = ['azure', 'network', 'vnet', 'delete',
                self.uuid(vnet.name)]
        return self.execute(cmd)

    def create_group(self, group):
        cmd  = ['azure', 'account', 'affinity-group', 'create']
        cmd += self.if_available('-l', group.location())
        cmd += ['-e', base64.b64encode(self.uuid(group.name))]
        cmd += [self.uuid(group.name)]

        print "----------------------------------------"
        print "Creating group: %s" % group.name
        print "Executing %s" % " ".join(cmd)

        return self.execute(cmd)

    def delete_group(self, group):
        for vm in group.virtual_machines(): self.delete_vm(vm)
        for vnet in group.virtual_networks(): self.delete_vnet(vnet)

        cmd  = ['azure', 'account', 'affinity-group', 'delete',
                self.uuid(group.name)]
        return self.execute(cmd)

env = Env('azure', "./benchmarks/fio/config.xml")
env.setup()
env.teardown()
