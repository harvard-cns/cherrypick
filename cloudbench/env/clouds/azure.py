import subprocess
import base64

from cloudbench import constants
from cloudbench.util import Debug

class AzureCloud(object):
    def __init__(self, env):
        self._env = env

    def namify(self, obj):
        return self._env.namify(obj)

    def execute(self, command):
        Debug.cmd << (' '.join(command)) << "\n"

        p = subprocess.Popen(' '.join(command), shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        (outdata, errdata) = p.communicate()

        if errdata: 
            Debug.err << errdata << "\n"

        if outdata:
            Debug.info << outdata << "\n"

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

        Debug.info << "Creating vm: %s\n" % vm.name
        ret = self.execute(cmd)
        if not ret:
            return ret

        # Create the endpoints of the vm
        for ep in vm.endpoints():
            ret = self.create_vm_endpoint(vm, ep)
            if not ret:
                return False

        return ret

    def create_vm_endpoint(self, vm, ep):
        cmd  = ['azure', 'vm', 'endpoint', 'create']
        cmd += [self.namify(vm), ep.public_port, ep.private_port]
        cmd += ['--endpoint-name', ep.name]
        cmd += ['--endpoint-protocol', ep.protocol]
        ret = self.execute(cmd)
        if not ret:
            Debug.err << "Failed to create the endpoint: %s" % ep
            return ret

    def start_vm(self, vm):
        cmd = ['azure', 'vm', 'start', self.namify(vm.name)]
        return self.execute(cmd)

    def stop_vm(self, vm):
        cmd = ['azure', 'vm', 'shutdown', self.namify(vm.name)]
        return self.execute(cmd)

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

        Debug.info << "Creating vnet: %s\n" % vnet.name
        return self.execute(cmd)

    def delete_vnet(self, vnet):
        for vm in vnet.virtual_machines(): vm.delete()

        cmd  = ['azure', 'network', 'vnet', 'delete', '-q',
                self.namify(vnet.name)]
        return self.execute(cmd)

    def hashify_22(self, name):
        import hashlib
        return str(hashlib.md5(name).hexdigest())[0:22]

    def create_group(self, group):
        cmd  = ['azure', 'account', 'affinity-group', 'create']
        cmd += self.if_available('-l', group.location())
        cmd += ['-e', base64.b64encode(self.namify(group.name))]
        cmd += [self.namify(group.name)]

        Debug.info << "Creating group: " << group.name << "\n"
        ret = self.execute(cmd)

        if not ret:
            Debug.err << "Failed to create the affinity group: " << \
            self.namify(group.name) << "\n"


        cmd  = ['azure', 'storage', 'account', 'create']
        cmd += ['-a', self.namify(group.name)]
        cmd += ['--type', group.storage_type]
        cmd += [self.hashify_22(self.namify(group.name))]

        return self.execute(cmd)

    def delete_group(self, group):
        for vm in group.virtual_machines(): vm.delete()
        for vnet in group.virtual_networks(): vnet.delete()

        cmd  = ['azure', 'storage', 'account', 'delete']
        cmd += ['-q', self.hashify_22(self.namify(group.name))]

        ret = self.execute(cmd)
        if not ret:
            Debug.err << "Couldn't delete the storage account of " << \
            group.name << "\n"

        cmd = ['azure', 'account', 'affinity-group', 'delete', '-q']
        cmd += [self.namify(group.name)]

        return self.execute(cmd)

