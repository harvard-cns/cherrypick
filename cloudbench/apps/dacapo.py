from cloudbench.util import Config

DACAPO_PATH='~/'
DACAPO_FILE='dacapo-9.12-bach.jar'

def install(vm):
    vm.install('openjdk6')
    vm.send(Config.path('tools', DACAPO_FILE), DACAPO_PATH)

def remove(vm):
    vm.rmdir(DACAPO_PATH)

def installed(vm):
    return vm.isdir(DACAPO_PATH)

