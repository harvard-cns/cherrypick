import subprocess
import base64

from cloudbench import constants
from cloudbench.util import Debug

from .base import Cloud

class AwsCloud(Cloud):
    def start_virtual_machine(self, vm):
        print 'Booting up (%s)' % vm
        return True

    def stop_virtual_machine(self, vm):
        print 'Stopping up (%s)' % vm
        return True

    def address_virtual_machine(self, vm):
        return self._env.namify(vm.name) + ".cloudapp.net"

    def hashify_22(self, name):
        import hashlib
        return str(hashlib.md5(name).hexdigest())[0:22]

    def create_location(self, group):
        print 'Initiating location (%s)' % group
        return True

    def create_security_group(self, ep):
        print 'Creating security group (%s)' % ep
        return True

    def create_virtual_machine(self, vm):
        print 'Creating virtual machine (%s)' % vm
        return True

    def create_virtual_network(self, vnet):
        print 'Creating virtual network (%s)' % vnet
        return True

    def delete_security_group(self, group):
        print "Deleting security group (%s)" % group
        return True

    def delete_virtual_machine(self, vm):
        print "Deleting virtual machine (%s)" % vm
        return True

    def delete_virtual_network(self, vnet):
        print "Deleting virtual network (%s)" % vnet
        return True

    def delete_location(self, group):
        print "Deleting location (%s)" % group
        return True

