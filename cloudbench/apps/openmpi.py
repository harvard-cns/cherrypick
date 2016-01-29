def install(vm):
    vm.package_manager.install('openmpi-bin')
    vm.package_manager.install('libopenmpi-dev')
    vm.package_manager.install('gfortran')

def installed(vm):
    pass

def uninstall(vm):
    pass
