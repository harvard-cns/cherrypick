def install(vm):
    vm.package_manager.install('python-software-properties')
    vm.execute('sudo add-apt-repository ppa:webupd8team/java')
    vm.execute('sudo aptitude update -y')
    vm.execute('"echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections"')
    vm.package_manager.install('oracle-java8-installer')

def installed(vm):
    pass


def remove(vm):
    vm.package_manager.remove('oracle-java8-installer')
