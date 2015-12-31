from cloudbench.util import Debug, parallel

from cloudbench.apps.cassandra import CASSANDRA_PATH
from cloudbench.cluster.cassandra import CassandraCluster

import re
import time

TIMEOUT=21600

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
            disk_id += 1
    parallel(setup_vm_disks, vms)

def cassandra_test(all_vms, env):
    testVmCount = len(all_vms)/3

    benchmarkVms = all_vms[:testVmCount]
    vms = all_vms[testVmCount:]

    parallel(lambda x: x.install('cassandra'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

    setup_disks(env, vms)

    parallel(setup_disk, vms)
    cluster = CassandraCluster(vms)
    cluster.kill()
    cluster.reset()
    cluster.setup()
    cluster.start()
    return

    output = {}

    output['write'] = cluster.stress_test_write(1000000)
    #output['read']  = cluster.stress_test_read()
    output['mix']   = cluster.stress_test_mixed(write=1, read=4)

    thread_count_max_throughtput = int(output['mix'].split("\n")[-6].split(" ")[0])

    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)
    
    output['throughput'] = cluster.stress_test_mixed_with_thread_count(
            write=1,
            read=4,
            count=1000000,
            thread_count=thread_count_max_throughtput)

    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)

    with open('throughput-' + cluster.seeds[0].type + '.throughput', 'w+') as f:
        f.write(output['throughput'].split("\n")[-3])

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, cassandra_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

