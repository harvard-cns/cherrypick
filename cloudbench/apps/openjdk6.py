def install(vm):
    vm.package_manager.install('openjdk-6-jre')

def installed(vm):
    pass

def remove(vm):
    vm.package_manager.remove('openjdk-6-jre')
