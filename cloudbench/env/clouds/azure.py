import subprocess
import base64
from cloudbench import constants

class AzureCloud(object):
    def __init__(self, env):
        self._env = env

    def namify(self, obj):
        return self._env.namify(obj)

    def execute(self, command):
        print "Running %s" % (' '.join(command))
        p = subprocess.Popen(' '.join(command), shell=True)
        return (p.wait() == 0)

    def if_available(self, option, value):
        if value:
            return [option,'"' + str(value) + '"']
        return []

    def create_vm(self, vm):
        cmd  = ['azure', 'vm', 'create', '-z', vm.type]
        cmd += self.if_available('-a', self.namify(vm.group()))
        cmd += self.if_available('-w', self.namify(vm.network()))
        cmd += ['-e', '22', self.namify(vm.name), vm.image,  'cloudbench', '-P',
                '-t', constants.DEFAULT_VM_PUBLIC_KEY]

        print "----------------------------------------"
        print "Creating vm: %s" % vm.name
        print "Executing %s" % " ".join(cmd)

        ret = self.execute(cmd)
        if not ret: return ret

        # Create the endpoints of the vm
        for ep in vm.endpoints():
            self.create_vm_endpoint(vm, ep)

    def create_vm_endpoint(self, vm, ep):
        cmd  = ['azure', 'vm', 'endpoint', 'create']
        cmd += [self.namify(vm), ep.public_port, ep.private_port]
        cmd += ['--endpoint-name', ep.name]
        cmd += ['--endpoint-protocol', ep.protocol]
        ret = self.execute(cmd)
        if not ret:
            print "Failed to create the endpoint: %s" % ep
            return ret

    def address_vm(self, vm):
        return self._env.namify(vm.name) + ".cloudapp.net"

    def delete_vm(self, vm):
        cmd = ['azure', 'vm', 'delete', '-b', '-q', self.namify(vm.name)]
        return self.execute(cmd)

    def create_vnet(self, vnet):
        cmd  = ['azure', 'network', 'vnet', 'create']
        cmd += self.if_available('-e', vnet.address_range())
        cmd += self.if_available('-l', vnet.location())
        cmd += self.if_available('-a', self.namify(vnet.group()))
        cmd += [self.namify(vnet.name)]

        print "----------------------------------------"
        print "Creating vnet: %s" % vnet.name
        print "Executing %s" % " ".join(cmd)

        return self.execute(cmd)

    def delete_vnet(self, vnet):
        for vm in vnet.virtual_machines(): self.delete_vm(vm)

        cmd  = ['azure', 'network', 'vnet', 'delete', '-q',
                self.namify(vnet.name)]
        return self.execute(cmd)

    def create_group(self, group):
        cmd  = ['azure', 'account', 'affinity-group', 'create']
        cmd += self.if_available('-l', group.location())
        cmd += ['-e', base64.b64encode(self.namify(group.name))]
        cmd += [self.namify(group.name)]

        print "----------------------------------------"
        print "Creating group: %s" % group.name
        print "Executing %s" % " ".join(cmd)

        return self.execute(cmd)

    def delete_group(self, group):
        for vm in group.virtual_machines(): self.delete_vm(vm)
        for vnet in group.virtual_networks(): self.delete_vnet(vnet)

        cmd  = ['azure', 'account', 'affinity-group', 'delete', '-q', 
                self.namify(group.name)]
        return self.execute(cmd)

