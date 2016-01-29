from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera
from cloudbench.cluster.base import Cluster
from cloudbench.apps.hivetpch import TPCH_HIVE_DIR
from cloudbench.util import Config

import re
import time

TIMEOUT=21600
TPCH_QUERIES=[2, 6, 11, 13, 14, 15, 16, 20]
TPCH_SCALE=2

def argos_start(vms):
    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

def argos_finish(vms):
    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)

    # Delete empty files
    parallel(lambda vm: vm.script('find ~/argos/proc -type f -empty -delete'), vms)
    # Delete empty directories
    parallel(lambda vm: vm.script('find ~/argos/proc -type d -empty -delete'), vms)

    # Save argos results
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)

    # Save argos output
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)

def setup_hadoop(env, vms):
    setup_base(env, vms)
    ce = Cloudera(vms)
    ce.install('Hadoop')
    return ce['Hadoop']

def setup_base(env, vms):
    parallel(lambda vm: vm.install('java8'), vms)
    parallel(lambda vm: vm.install('cloudera'), vms)
    parallel(lambda vm: vm.install('git'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

def setup_spark(env, vms):
    setup_base(env, vms)
    ce = Cloudera(vms)
    ce.install('Hadoop')
    ce.install('Spark')
    return ce['Spark']

def run_spark(vms, env):
    # install the spark-perf
    # update the config.py file ... mark mllib stuff as on
        # OptionSet("num-partitions", [128], can_scale=True) -- set 128 to the number of cores in the cluster
    # etc. etc.

    # Setup ssh keys
    cluster = Cluster(vms, user='ubuntu')
    cluster.setup_keys()

    # Setup disks
    setup_disks(env, vms)

    # Setup spark
    spark = setup_spark(env, vms)

    # Setup spark perf
    setup_spark_perf(env, vms)

    # Make sure spark can be written by anyone
    parallel(lambda vm: vm.script('chown -R ubuntu:ubuntu /var/lib/spark/work'), vms)
    parallel(lambda vm: vm.script('sudo -u hdfs hdfs dfs -chmod 777 /user/spark'), vms)

    argos_start(vms)
    spark.master.script('cd /home/ubuntu/spark-perf; /usr/bin/time -f \'%e\' -o out.time ./bin/run >log.out 2>&1')
    argos_finish(vms)

    spark_time = spark.master.script('cd /home/ubuntu/spark-perf; tail -n1 out.time').strip()
    spark_out = spark.master.script('cd /home/ubuntu/spark-perf; cat log.out').strip()
    file_name = str(time.time()) + '-' + spark.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write("0," + str(spark_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(spark_out)

def setup_spark_perf(env, vms):
    path = Config.path('tools', 'spark-perf.tar.gz')
    parallel(lambda vm: vm.send(path, '/home/ubuntu'), vms)
    parallel(lambda vm: vm.script('rm -rf /home/ubuntu/spark-perf'), vms)
    parallel(lambda vm: vm.script('tar -xzf spark-perf.tar.gz'), vms)
    num_cores = len(vms) * vms[0].cpus()

    def replace_line(vm):
        vm.script("cd spark-perf; sed -i '/OptionSet(\"num-partitions\", \[128\], can_scale=True),/c\    OptionSet(\"num-partitions\", [%d], can_scale=False),' config/config.py" % num_cores )
    parallel(replace_line, vms)

def setup_disks(env, vms):
    def setup_vm_disks(vm):
        root = vm.root_disk()
        disks = vm.disks()
        disk_id = 2

        if len(disks) == 0:
            disks = vm.local_disks_except_root()

        for disk in disks:
            if root.startswith(disk):
                continue
            vm.mount(disk, '/data/%d' % disk_id, force_format=True)
            vm.script("chmod 777 -R /data/%d" % disk_id)
            disk_id += 1
    parallel(setup_vm_disks, vms)

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, run_spark)
    env.benchmark.executor.run()
