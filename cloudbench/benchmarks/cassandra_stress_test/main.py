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
            vm.script("chmod 777 -R /data/%d" % disk_id)
            disk_id += 1
    parallel(setup_vm_disks, vms)

def cassandra_test(all_vms, env):
    test_vm_count = len(all_vms)/3

    benchmark_vms = all_vms[:test_vm_count]
    vms = all_vms[test_vm_count:]

    parallel(lambda x: x.install('cassandra'), all_vms)
    parallel(lambda vm: vm.install('argos'), vms)

    setup_disks(env, vms)
    cluster = CassandraCluster(vms, benchmark_vms)
    cluster.kill()
    cluster.reset()
    cluster.setup()
    cluster.start()

    output = {}

    output['write'] = cluster.stress_test_write(int(env.param('cassandra:record_count')))
    #output['read']  = cluster.stress_test_read()
    output['mix']   = cluster.stress_test_mixed(write=1, read=4)

    thread_count_max_throughtput = int(output['mix'][0].split("\n")[-6].split(" ")[0])

    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)
    
    output['throughput'] = cluster.stress_test_mixed_with_thread_count(
            write=1,
            read=4,
            count=int(env.param('cassandra:record_count')),
            thread_count=thread_count_max_throughtput)

    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)

    idx = 0
    for thr in output['throughput']:
        with open('throughput-'  + str(idx) + '-' + cluster.seeds[0].type + '.throughput', 'w+') as f:
            f.write(thr.split("\n")[-3])
        with open('log-'  + str(idx) + '-' + cluster.seeds[0].type + '.throughput', 'w+') as f:
            f.write(thr)
        idx += 1

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, cassandra_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

