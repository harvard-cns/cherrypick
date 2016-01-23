from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera
from cloudbench.apps.hivetpch import TPCH_HIVE_DIR

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
    parallel(lambda vm: vm.install('hivetpch'), vms)
    parallel(lambda vm: vm.install('tpch_rxin'), vms)

def setup_spark(env, vms):
    setup_base(env, vms)
    ce = Cloudera(vms)
    ce.install('Hadoop')
    ce.install('Spark')
    return ce['Spark']

def setup_hive(env, vms):
    setup_base(env, vms)
    ce = Cloudera(vms)
    ce.install('Hive')
    return ce['Hive']

def terasort(vms, env):
    hadoop = setup_hadoop(env, vms)
    print "Master is: %s" % hadoop.master.name

    hadoop.execute('sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5.5.0.jar teragen -D mapred.map.tasks=100 300000000 /terasort-input')

    hadoop.execute('/usr/bin/time -f \'%e\' -o terasort.out sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5.5.0.jar terasort -D mapred.reduce.tasks=20 /terasort-input /terasort-output')

def spark(vms, env):
    spark = setup_spark(env, vms)

def hive(vms, env):
    hive = setup_hive(env, vms)
    return

def tpch_cmd(cmd):
    return 'cd ~/hive-testbench && %s' % cmd

def tpch_run_query(master, query, scale):
    master.script(tpch_cmd('/usr/bin/time -f \'%e\' -o timeout-{0}.out hive -i sample-queries-tpch/testbench.settings --database tpch_flat_orc_{0} -f {2}/q{1}_*.hive'.format(scale, query, TPCH_HIVE_DIR)))


def tpch(vms, env):
    hive = setup_hive(env, vms)
    hive.master.script(tpch_cmd('./tpch-setup.sh {0}'.format(TPCH_SCALE)))

    def execute_query(num):
        tpch_run_query(hive.master, num, TPCH_SCALE)

    start = time.time()
    parallel(execute_query, TPCH_QUERIES)
    end = time.time()
    print "Total time: %.2f" % (end - start)

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

def ycsb(vms, env):
    from cloudbench.cluster.cassandra import CassandraCluster
    parallel(lambda vm: vm.install('cassandra'), vms)
    partition_length = len(vms)/3
    t_vms = vms[:partition_length]
    c_vms = vms[partition_length:]

    setup_disks(env, vms)
    cluster = CassandraCluster(c_vms, t_vms)
    cluster.kill()
    cluster.reset()
    cluster.setup()
    cluster.start()

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, spark)
    env.benchmark.executor.run()
