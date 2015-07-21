from cloudbench.util import Config

COREMARK_PATH='~/coremark'
COREMARK_FILE='coremark_v1.0.tgz'
COREMARK_DIR='coremark_v1.0'
COREMARK_REMOTE_PATH='{0}/{1}'.format(COREMARK_PATH, COREMARK_DIR)

def install(vm):
    vm.mkdir(COREMARK_PATH)
    vm.package_manager.install('build-essential')
    vm.send(Config.path('tools', COREMARK_FILE), COREMARK_PATH)

    vm.cd(COREMARK_PATH).execute('tar xzf {0}'.format(COREMARK_FILE))

def remove(vm):
    vm.rmdir(COREMARK_PATH)

def installed(vm):
    return vm.isdir(COREMARK_PATH)

