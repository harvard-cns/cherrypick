from cloudbench.apps.hadoop import HADOOP_USER, HADOOP_DIR

def install(vm):
    vm.script('rm -rf Big-Data-Behcnmark-for-Big-Bench')
    vm.install('git')
    vm.script('sudo su - {0} -c "rm -rf Big-Data-Behcnmark-for-Big-Bench"'.format(HADOOP_USER))
    vm.script('sudo su - {0} -c "git clone https://github.com/SiGe/Big-Data-Benchmark-for-Big-Bench.git"'.format(HADOOP_USER))
