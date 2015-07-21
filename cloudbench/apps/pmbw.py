from cloudbench.util import Config

PMBW_PATH='~/pmbw'
PMBW_FILE='pmbw-0.6.2.tar.bz2'
PMBW_DIR='pmbw-0.6.2'
PMBW_REMOTE_PATH='{0}/{1}'.format(PMBW_PATH, PMBW_DIR)

def install(vm):
    vm.mkdir(PMBW_PATH)
    vm.package_manager.install('build-essential')
    vm.send(Config.path('tools', PMBW_FILE), PMBW_PATH)

    with vm.cd(PMBW_PATH) as cxt:
        cxt.execute('tar xjf {0}'.format(PMBW_FILE))
        cxt.execute('./configure')
        cxt.execute('./make')

def remove(vm):
    vm.rmdir(PMBW_PATH)

def installed(vm):
    return vm.isdir(PMBW_PATH)

