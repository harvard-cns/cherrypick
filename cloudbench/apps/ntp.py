from cloudbench.util import Config
import time

def install(vm):
    # vm.package_manager.install('ntp')
    # time.sleep(2)
    # vm.script('service ntp restart');
    # time.sleep(2)
    vm.script("ntp-wait")

def remove(vm):
    #TODO: Delete ntp
    pass

def installed(vm):
    #TODO: verify if ntp is installed
    #return vm.isdir(ARGOS_PATH + '/argos')
    return False

