import subprocess
import base64

from cloudbench import constants
from cloudbench.util import Debug

from .base import Cloud

class AzureCloud(Cloud):
    def start_vm(self, vm):
        cmd = ['azure', 'vm', 'start', self.namify(vm.name)]
        return self.execute(cmd)

    def stop_vm(self, vm):
        cmd = ['azure', 'vm', 'shutdown', self.namify(vm.name)]
        return self.execute(cmd)

    def address_vm(self, vm):
        return self._env.namify(vm.name) + ".cloudapp.net"

    def hashify_22(self, name):
        import hashlib
        return str(hashlib.md5(name).hexdigest())[0:22]

    def create_location(self, group):
        # cmd  = ['azure', 'storage', 'account', 'create']
        # cmd += ['-a', self.namify(group.name)]
        # cmd += ['--type', group.storage_type]
        # cmd += [self.hashify_22(self.namify(group.name))]

        return self.execute(cmd)
        cmd  = ['azure', 'account', 'affinity-group', 'create']
        cmd += self.if_available('-l', group.location)
        cmd += ['-e', base64.b64encode(self.unique(group.name))]
        cmd += [self.unique(group.name)]

        return self.execute(cmd)

    def create_security_group(self, ep):
        ret = True
        for vm in ep.virtual_machines():
            cmd  = ['azure', 'vm', 'endpoint', 'create']
            cmd += [self.unique(vm), ep.public_port, ep.private_port]
            cmd += ['--endpoint-name', self.unique(ep.name)]
            cmd += ['--endpoint-protocol', ep.protocol]

            ret = self.execute(cmd)

            if ret is False:
                return False

        return ret

    def create_virtual_machine(self, vm):
        cmd  = ['azure', 'vm', 'create', '-z', vm.type]
        cmd += self.if_available('-a', self.unique(vm.location()))
        cmd += self.if_available('-w', self.unique(vm.virtual_network()))
        cmd += ['-e', '22', self.unique(vm.name), vm.image,  'cloudbench', '-P',
                '-t', constants.DEFAULT_VM_PUBLIC_KEY]

        return self.execute(cmd)

    def create_virtual_network(self, vnet):
        cmd  = ['azure', 'network', 'vnet', 'create']
        cmd += self.if_available('-e', vnet.address_range())
        cmd += self.if_available('-l', vnet.location())
        cmd += self.if_available('-a', self.unique(vnet.group()))
        cmd += [self.unique(vnet.name)]

        return self.execute(cmd)

    def delete_security_group(self, group):
        print "Deleting security group"
        return True

    def delete_virtual_machine(self, vm):
        cmd = ['azure', 'vm', 'delete', '-b', '-q', self.unique(vm.name)]
        return self.execute(cmd)

    def delete_virtual_network(self, vnet):
        cmd  = ['azure', 'network', 'vnet', 'delete', '-q', self.unique(vnet.name)]
        return self.execute(cmd)

    def delete_location(self, group):
        cmd = ['azure', 'account', 'affinity-group', 'delete', '-q']
        cmd += [self.unique(group.name)]
        return self.execute(cmd)

