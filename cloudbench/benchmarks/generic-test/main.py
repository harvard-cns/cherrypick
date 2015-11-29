from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera

import re
import time

TIMEOUT=21600
TPCH_QUERIES=[1,3,4,5]

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

def tpch_cmd(cmd):
    return 'sudo su - hduser -c "cd hive-testbench && %s"' % cmd

def tpch_run_query(master, query, scale):
    master.script(tpch_cmd('/usr/bin/time -f \'%e\' -o timeout-{0}.out hive -i sample-queries-tpch/testbench.settings --database tpch_flat_orc_{0} -f sample-queries-tpch/tpch_query{1}.sql'.format(scale, query)))


def tpch(vms, env):
    hive = setup_hive(env, vms)
    parallel(lambda vm: vm.install('tpch'), vms)
    hive.master.script(tpch_cmd('./tpch-setup.sh {0}'.format(TPCH_SCALE)))
    return

    start = time.time()
    for query in TPCH_QUERIES:
        tpch_run_query(hive.master, query, TPCH_SCALE)
    end = time.time()
    print "Total time: %.2f" % (end - start)

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, spark)
    env.benchmark.executor.run()
