from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera
from cloudbench.apps.hivetpch import TPCH_HIVE_DIR

import os
import random
import re
import time

TIMEOUT=21600
BASE_QUERIES=[2, 6, 11, 13, 14, 15, 16, 20]

rng = random.Random()
rng.seed(4)
TPCH_QUERIES=[rng.choice(BASE_QUERIES) for i in range(1,20)]

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
    setup_disks(vms, env)
    setup_base(vms, env)

    ce = Cloudera(vms)
    ce.install('Hadoop')
    ce.install('Hive')

    return ce['Hive']

def setup_disks(vms, env):
    def setup_vm_disks(vm):
        vm.script('rm -rf /data/1/')
        root = vm.root_disk()
        disks = vm.disks()
        disk_id = 2

        if len(disks) == 0 or vm.type == 'i2.8xlarge':
            disks = vm.local_disks_except_root()

        for disk in disks:
            if root.startswith(disk):
                continue
            vm.mount(disk, '/data/%d' % disk_id, force_format=True)
            disk_id += 1
    parallel(setup_vm_disks, vms)


def tpch_cmd(cmd):
    return 'cd ~/hive-testbench && %s' % cmd

def tpch_run_query(master, query, scale):
    master.script(tpch_cmd('/usr/bin/time -f \'%e\' -o timeout-{0}.out hive -i sample-queries-tpch/testbench.settings --database tpch_flat_orc_{0} -f {2}/q{1}_*.hive 2>err-{1}.log 1>run.log'.format(scale, query, TPCH_HIVE_DIR)))

def makedirectory(name):
    if not os.path.exists(name):
        os.makedirs(name)

def tpch(vms, env):
    tpch_scale = int(env.param('tpch:scale'))
    hive = setup_hive(vms, env)
    hive.master.script(tpch_cmd('./tpch-setup.sh {0} >/dev/null 2>&1'.format(tpch_scale)))

    directory='tpch-' + hive.master.type + '-' + str(len(vms)) + "-results"
    makedirectory(directory)

    def execute_query(query):
        tpch_run_query(hive.master, query, tpch_scale)

    for iteration in range(1, int(env.param('tpch:runs'))):
        # Drop file caches to be more accurate for amount of reads and writes
        parallel(lambda vm: vm.script("sync; echo 3 > /proc/sys/vm/drop_caches"), vms)
        argos_start(vms, directory, iteration)
        start = time.time()
        parallel(execute_query, TPCH_QUERIES)
        end = time.time()
        argos_finish(vms, directory, iteration)
        
        file_name = str(time.time()) + '-' + hive.master.type
        with open(os.path.join(directory, str(iteration), hive.master.type + '.time'), 'w+') as f:
            f.write('0,%s' % str(end - start))

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, tpch)
    env.benchmark.executor.run()
