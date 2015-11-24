def install(vm):
    vm.install('unzip')
    vm.install('build-essential')
    vm.script('sudo su - hduser -c "git clone https://github.com/hortonworks/hive-testbench.git"')
    vm.script('sudo su - hduser -c "cd hive-testbench && ./tpch-build.sh"')

def uninstall(vm):
    pass

def installed(vm):
    pass
