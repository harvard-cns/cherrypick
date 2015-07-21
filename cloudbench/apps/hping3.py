PROGRAM='hping3'

def install(vm):
    return vm.package_manager.install(PROGRAM)

def is_installed(vm):
    return vm.package_manager.has(PROGRAM)

def remove(vm):
    return vm.package_manager.remove(PROGRAM)
