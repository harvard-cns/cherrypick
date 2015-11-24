from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.hadoop import HADOOP_USER
from cloudbench.cluster.hadoop import HadoopCluster
from cloudbench.cluster.hive import HiveCluster

import re
import time

TIMEOUT=21600

TPCH_SCALE=5
TPCH_QUERIES=[1,2,3,4,5,6,7,8,10,11,12,14,15,16,17,19,20,22]
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

def setup_hive(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('hive'), vms)
    parallel(lambda vm: vm.install('mahout'), vms)
    parallel(lambda vm: vm.install('bigbench'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

    vms[0].install('bigbench')

    hadoop = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk'))
    hadoop.setup()
    hadoop.reset()

    hive = HiveCluster(hadoop)
    hive.setup()

    return hive

def tpch_cmd(cmd):
    return 'sudo su - hduser -c "cd hive-testbench && %s"' % cmd

def tpch_run_query(master, query, scale):
    master.script(tpch_cmd('/usr/bin/time -f \'%e\' -o timeout-{0}.out hive -i sample-queries-tpch/testbench.settings --database tpch_flat_orc_{0} -f sample-queries-tpch/tpch_query{1}.sql'.format(scale, query)))


def tpch(vms, env):
    hive = setup_hive(vms, env)
    parallel(lambda vm: vm.install('tpch'), vms)

    hive.master.script(tpch_cmd('./tpch-setup.sh {0}'.format(TPCH_SCALE)))

    argos_start(vms)
    start = time.time()
    for query in TPCH_QUERIES:
        tpch_run_query(hive.master, query, TPCH_SCALE)
    end = time.time()
    argos_finish(vms)
        
    file_name = str(time.time()) + '-' + hive.master.type
    with open(file_name + '.time', 'w+') as f:
        f.write(str(end - start))

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, tpch)
    env.benchmark.executor.run()
