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

class LocalCloud(Cloud):
    def __init__(self, *args, **kwargs):
        super(LocalCloud, self).__init__(*args, **kwargs)
        constants.DEFAULT_VM_USERNAME = 'harry'
        constants.DEFAULT_VM_PRIVATE_KEY= '~/.ssh/id_rsa'

    def execute(self, command, obj={}):
        ret = super(LocalCloud, self).execute(command, obj)
        return ret

    def start_virtual_machine(self, vm):
        """ Start a virtual machine """
        vm._started = True
        return

    def stop_virtual_machine(self, vm):
        """ Stop a virtual machine """
        vm._started = False
        return True

    def status_virtual_machine(self, vm):
        return vm._started

    def exists_virtual_machine(self, vm):
        return True

    def address_virtual_machine(self, vm):
        """ Returns the address of a vm """
        return vm.name

    def hashify_22(self, name):
        import hashlib
        return str(hashlib.md5(name).hexdigest())[0:22]

    def create_location(self, group):
        return True

    def create_security_group(self, ep):
        return None

    def create_virtual_machine(self, vm):
        return True

    def create_virtual_network(self, vnet):
        return True

    def delete_security_group(self, _):
        return True

    def delete_virtual_machine(self, virtual_machine):
        return True

    def delete_virtual_network(self, vnet):
        return True

    def delete_location(self, group):
        return True
