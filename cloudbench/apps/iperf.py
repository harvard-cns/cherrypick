PROGRAM='iperf'

def install(vm):
    return vm.package_manager.install(PROGRAM)

def installed(vm):
    return vm.package_manager.installed(PROGRAM)

def remove(vm):
    return vm.package_manager.remove(PROGRAM)
