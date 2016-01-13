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

def terasort(vms, env):
    hadoop = setup_hadoop(env, vms)
    print "Master is: %s" % hadoop.master.name

    hadoop.execute('sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5.5.0.jar teragen -D mapred.map.tasks={0} {1} /terasort-input'.format(env.param('terasort:mappers'), env.param('terasort:rows')))

    argos_start(vms)
    hadoop.execute('/usr/bin/time -f \'%e\' -o terasort.out sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5.5.0.jar terasort -D mapred.reduce.tasks={0} /terasort-input /terasort-output'.format(env.param('terasort:reducers')))
    argos_finish(vms)

    terasort_time = cluster.master.script('tail -n1 terasort.out').strip()
    terasort_out = cluster.master.script('cat output.log').strip()
    file_name = str(time.time()) + '-' + cluster.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write(str(teragen_time) + "," + str(terasort_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(terasort_out)

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, tpch)
    env.benchmark.executor.run()
