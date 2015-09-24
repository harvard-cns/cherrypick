import subprocess
import base64

from cloudbench import constants
from cloudbench.util import Debug, parallel, rate_limit

from .base import Cloud

from threading import RLock

import time

def disable(func):
    def func(*args, **kwargs):
        return True

    return func

class AzureCloud(Cloud):
    def __init__(self, *args, **kwargs):
        super(AzureCloud, self).__init__(*args, **kwargs)
        self.vnet_lock = RLock()
        self.pace_lock = RLock()
        self.pace_timer = 300

    # Is only allowed to be called once every 5 seconds
    # TODO: Why is there a limitation like this on Azure ... 5 seconds
    # wait per request is too much ...
    #@rate_limit(0.2)
    def execute(self, command, obj={}):
        ret = super(AzureCloud, self).execute(command, obj)

        # If we are too fast, backoff for 5 minutes before continuing again
        if 'Too many requests received' in obj['stderr']:
            print "Sleeping for 5 minutes:\n > %s, %s, %s" % (command, obj['stderr'], obj['stdout'])
            time.sleep(self.pace_timer)
            return self.execute(command, obj)

        return ret


    def start_virtual_machine(self, vm):
        """ Start a virtual machine """
        cmd = ['azure', 'vm', 'start', self.unique(vm.name)]
        vm._started = True
        return self.execute(cmd)

    def stop_virtual_machine(self, vm):
        """ Stop a virtual machine """
        cmd = ['azure', 'vm', 'shutdown', self.unique(vm.name)]
        vm._started = False
        return self.execute(cmd)

    def status_virtual_machine(self, vm):
        return vm._started

        # cmd = ['azure', 'vm', 'show', self.unique(vm.name)]
        # 
        # output = {}
        # self.execute(cmd, output)
        # if 'ReadyRole' in output['stdout']:
        #     return True
        # if 'Stopped' in output['stdout']:
        #     return False
        # return None

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
        def create_endpoint(vm):
            cmd = ['azure', 'vm', 'endpoint', 'create']
            cmd += [self.unique(vm), ep.public_port, ep.private_port]
            cmd += ['--name', self.unique(ep.name)[-15:]] # Endpoint name should be at most 15 characters
            cmd += ['--protocol', ep.protocol]
            self.execute(cmd)

        parallel(create_endpoint, ep.virtual_machines())
        return ret

    def create_virtual_machine(self, vm):
        """ Create a virtual machine """
        cmd = ['azure', 'vm', 'create', '-z', vm.type]
        cmd += self.if_available('-a', self.unique(vm.location()))
        cmd += self.if_available('-w', self.unique(vm.virtual_network()))
        cmd += ['-e', '22', self.unique(vm.name), vm.image, 'cloudbench', '-P',
                '-t', constants.DEFAULT_VM_PUBLIC_KEY]

        ret = self.execute(cmd)
        return True

    def create_virtual_network(self, vnet):
        """ Create a virtual network """
        # Azure cannot create multiple VNets together, lock on creation
        # of each VNet
        self.vnet_lock.acquire()
        ret = False
        try:
            cmd = ['azure', 'network', 'vnet', 'create']
            cmd += self.if_available('-e', vnet.address_range)
            cmd += self.if_available('-a', self.unique(vnet.location()))
            cmd += [self.unique(vnet.name)]

            ret = self.execute(cmd)
        finally:
            self.vnet_lock.release()
        return True

    def delete_security_group(self, _):
        """ Delete an azure 'security-group' a.k.a. an endpoint.

        We do not need to delete anything here, Azure takes care of it when we wipe out the machine"""

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
