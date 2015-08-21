from cloudbench.util import Config

LAMA_PATH='~/'
LAMA_FILE='lama.tar.gz'

def install(vm):
    vm.mkdir(LAMA_PATH)
    vm.package_manager.install('build-essential')
    vm.package_manager.install('python3-pip')
    vm.script('sudo pip3 install ntplib')

    vm.send(Config.path('tools', LAMA_FILE), LAMA_PATH)

    vm.cd(LAMA_PATH).execute('tar xzf {0}'.format(LAMA_FILE))

def remove(vm):
    vm.rmdir(LAMA_PATH)

def installed(vm):
    return vm.isdir(LAMA_PATH)

