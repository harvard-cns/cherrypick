from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera
from cloudbench.apps.hivetpch import TPCH_HIVE_DIR

import os
import re
import time

TIMEOUT=21600

TPCH_SCALE=5
TPCH_QUERIES=[2, 6, 11, 13, 14, 15, 16, 20]

def argos_start(vms, directory, iteration):
    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

def argos_finish(vms, directory, iteration):
    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)

    # Delete empty files
    parallel(lambda vm: vm.script('find ~/argos/proc -type f -empty -delete'), vms)
    # Delete empty directories
    parallel(lambda vm: vm.script('find ~/argos/proc -type d -empty -delete'), vms)

    subdir=os.path.join(directory, str(iteration))
    makedirectory(subdir)

    # Save argos results
    parallel(lambda vm: vm.recv('~/argos/proc', os.path.join(subdir, vm.name + '-proc')), vms)

    # Save argos output
    parallel(lambda vm: vm.recv('~/argos/argos.out', os.path.join(subdir, vm.name + '-argos.out')), vms)


def setup_base(vms, env):
    parallel(lambda vm: vm.install('java8'), vms)
    parallel(lambda vm: vm.install('argos'), vms)
    parallel(lambda vm: vm.install('hivetpch'), vms)
    parallel(lambda vm: vm.install('tpch_rxin'), vms)
    parallel(lambda vm: vm.install('cloudera'), vms)

def setup_hive(vms, env):
    setup_base(vms, env)

    ce = Cloudera(vms)
    ce.install('Hadoop')
    ce.install('Hive')

    return ce['Hive']

def tpch_cmd(cmd):
    return 'cd ~/hive-testbench && %s' % cmd

def tpch_run_query(master, query, scale):
    master.script(tpch_cmd('/usr/bin/time -f \'%e\' -o timeout-{0}.out hive -i sample-queries-tpch/testbench.settings --database tpch_flat_orc_{0} -f {2}/q{1}_*.hive'.format(scale, query, TPCH_HIVE_DIR)))

def makedirectory(name):
    if not os.path.exists(name):
        os.makedirs(name)

def tpch(vms, env):
    hive = setup_hive(vms, env)
    hive.master.script(tpch_cmd('./tpch-setup.sh {0}'.format(TPCH_SCALE)))

    directory='tpch-' + hive.master.type + "-results"
    makedirectory(directory)

    def execute_query(query):
        tpch_run_query(hive.master, query, TPCH_SCALE)

    for iteration in range(1, 6):
        argos_start(vms, directory, iteration)
        start = time.time()
        parallel(execute_query, TPCH_QUERIES)
        end = time.time()
        argos_finish(vms, directory, iteration)
        
        file_name = str(time.time()) + '-' + hive.master.type
        with open(os.path.join(directory, str(iteration), hive.master.type + '.time'), 'w+') as f:
            f.write(str(end - start))

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, tpch)
    env.benchmark.executor.run()
