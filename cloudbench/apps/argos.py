from cloudbench.util import Config

ARGOS_PATH='~/'
ARGOS_FILE='argos.tar.gz'

def install(vm):
    vm.package_manager.install('build-essential')
    vm.package_manager.install('autoconf')
    vm.package_manager.install('libmnl0')
    vm.package_manager.install('libmnl-dev')
    vm.package_manager.install('libpcap-dev')

    vm.script("rm -rf ~/argos");
    vm.send(Config.path('tools', ARGOS_FILE), ARGOS_PATH)
    vm.cd(ARGOS_PATH).execute('tar xzf {0}'.format(ARGOS_FILE));
    vm.cd(ARGOS_PATH + '/argos').execute('autoreconf --install')
    vm.cd(ARGOS_PATH + '/argos').execute('./configure && make')

def remove(vm):
    vm.rmdir(ARGOS_PATH + '/argos')

def installed(vm):
    return vm.isdir(ARGOS_PATH + '/argos')

