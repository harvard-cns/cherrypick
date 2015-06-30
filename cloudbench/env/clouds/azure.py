import subprocess
import base64

from cloudbench import constants
from cloudbench.util import Debug, parallel

from .base import Cloud

from threading import RLock

import time

class AzureCloud(Cloud):
    def __init__(self, *args, **kwargs):
        super(AzureCloud, self).__init__(*args, **kwargs)
        self.vnet_lock = RLock()
        self.pace_lock = RLock()
        self.pace_timer = 300

    def execute(self, command, obj={}):
        ret = super(AzureCloud, self).execute(command, obj)

        # If we are too fast, backoff for 5 minutes before continuing again
        if 'Too many requests received' in obj['stderr']:
            print "Sleeping for 5 minutes: %s, %s, %s" % (command, obj['stderr'], obj['stdout'])
            time.sleep(self.pace_timer)
            return self.execute(command, obj)

        return ret


    def start_virtual_machine(self, vm):
        """ Start a virtual machine """
        cmd = ['azure', 'vm', 'start', self.unique(vm.name)]
        return self.execute(cmd)

    def stop_virtual_machine(self, vm):
        """ Stop a virtual machine """
        cmd = ['azure', 'vm', 'shutdown', self.unique(vm.name)]
        return self.execute(cmd)

    def status_virtual_machine(self, vm):
        cmd = ['azure', 'vm', 'show', self.unique(vm.name)]
        
        output = {}
        self.execute(cmd, output)
        if 'ReadyRole' in output['stdout']:
            return True
        if 'Stopped' in output['stdout']:
            return False
        return None

    def exists_virtual_machine(self, vm):
        cmd = ['azure', 'vm', 'show', self.unique(vm.name)]
        output = {}
        self.execute(cmd, output)
        return 'No VMs found' in output['stdout']

    def address_virtual_machine(self, vm):
        """ Returns the address of a vm """
        # TODO: Change the name to address_virtual_machine
        return self.unique(vm.name) + ".cloudapp.net"

    def hashify_22(self, name):
        import hashlib
        return str(hashlib.md5(name).hexdigest())[0:22]

    def create_location(self, group):
        """ Create an affinity group in microsoft terms """
        # cmd  = ['azure', 'storage', 'account', 'create']
        # cmd += ['-a', self.unique(group.name)]
        # cmd += ['--type', group.storage_type]
        # cmd += [self.hashify_22(self.unique(group.name))]

        # return self.execute(cmd)
        cmd = ['azure', 'account', 'affinity-group', 'create']
        cmd += self.if_available('-l', group.location)
        cmd += ['-e', base64.b64encode(self.unique(group.name))]
        cmd += [self.unique(group.name)]

        self.execute(cmd)

        # TODO: creating a location tends to fail because we can't
        # cleanly delete it ... for now return true on creating a
        # location
        return True

    def create_security_group(self, ep):
        """ Create endpoints in the microsoft terms """
        ret = True
        # TODO: Can parallelize here
        for vm in ep.virtual_machines():
            cmd = ['azure', 'vm', 'endpoint', 'create']
            cmd += [self.unique(vm), ep.public_port, ep.private_port]
            cmd += ['--endpoint-name', self.unique(ep.name)]
            cmd += ['--endpoint-protocol', ep.protocol]

            ret = self.execute(cmd)

            if ret is False:
                return False

        return ret

    def create_virtual_machine(self, vm):
        """ Create a virtual machine """
        cmd = ['azure', 'vm', 'create', '-z', vm.type]
        cmd += self.if_available('-a', self.unique(vm.location()))
        cmd += self.if_available('-w', self.unique(vm.virtual_network()))
        cmd += ['-e', '22', self.unique(vm.name), vm.image, 'cloudbench', '-P',
                '-t', constants.DEFAULT_VM_PUBLIC_KEY]

        return self.execute(cmd)

    def create_virtual_network(self, vnet):
        """ Create a virtual network """
        # Azure cannot create multiple VNets together, lock on creation
        # of each VNet
        self.vnet_lock.acquire()
        ret = False
        try:
            cmd = ['azure', 'network', 'vnet', 'create']
            cmd += self.if_available('-e', vnet.address_range)
            #cmd += self.if_available('-l', vnet.location())
            cmd += self.if_available('-a', self.unique(vnet.location()))
            cmd += [self.unique(vnet.name)]

            ret = self.execute(cmd)
        finally:
            self.vnet_lock.release()
        return ret

    def delete_security_group(self, _):
        """ Delete an azure 'security-group' a.k.a. an endpoint.

        We don't actually delete anything here, it's just a method that
        should be provided by the cloud interface """

        print "Deleting security group"
        return True

    def delete_virtual_machine(self, virtual_machine):
        """ Delete a virtual machine and the associated storage """
        cmd = ['azure', 'vm', 'delete', '-b', '-q', self.unique(virtual_machine.name)]
        return self.execute(cmd)

    def delete_virtual_network(self, vnet):
        """ Delete a virtual network """
        # Serialize network creation
        self.vnet_lock.acquire()
        ret = False
        try:
            cmd = ['azure', 'network', 'vnet', 'delete', '-q', self.unique(vnet.name)]
            ret = self.execute(cmd)
        finally:
            self.vnet_lock.release()

        return ret

    def delete_location(self, group):
        cmd = ['azure', 'account', 'affinity-group', 'delete', '-q']
        cmd += [self.unique(group.name)]
        self.execute(cmd)

        # TODO: creating a location tends to fail because we can't
        # cleanly delete it ... for now return true on creating a
        # location
        return True
