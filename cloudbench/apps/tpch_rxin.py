def install(vm):
    vm.install('unzip')
    vm.install('build-essential')
    vm.install('git')
    vm.script('git clone https://github.com/hortonworks/hive-testbench.git')
    vm.script('chown -R ubuntu:ubuntu ~/hive-testbench')
    vm.script('cd hive-testbench && ./tpch-build.sh')
    vm.script('echo "set hive.exec.parallel=true;" >> ~/hive-testbench/sample-queries-tpch/testbench.settings')

def uninstall(vm):
    pass

def installed(vm):
    pass
