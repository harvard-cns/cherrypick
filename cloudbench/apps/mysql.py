def install(vm):
    vm.script('export DEBIAN_FRONTEND=noninteractive; apt-get install -y mysql-server')
    vm.package_manager.install('libmysql-java')

def uninstall(vm):
    pass

def installed(vm):
    pass
