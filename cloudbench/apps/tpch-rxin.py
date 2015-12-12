def install(vm):
    vm.install('unzip')
    vm.install('build-essential')
    vm.script('git clone https://github.com/hortonworks/hive-testbench.git')
    vm.script('chown -R ubuntu:ubuntu ~/hive-testbench')
    vm.script('cd hive-testbench && ./tpch-build.sh')

def uninstall(vm):
    pass

def installed(vm):
    pass
