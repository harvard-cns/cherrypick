from cloudbench.util import Debug, parallel

from cloudbench.apps.cassandra import CASSANDRA_PATH
from cloudbench.cluster.cassandra import CassandraCluster

from cloudbench.apps.ycsb import YCSB_PATH

from threading import RLock

import re
import time

TIMEOUT=21600


YcsbTemplate="""
create keyspace ycsb WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': 3 };
USE ycsb;
create table usertable (
    y_id varchar primary key,
    field0 varchar,
    field1 varchar,
    field2 varchar,
    field3 varchar,
    field4 varchar,
    field5 varchar,
    field6 varchar,
    field7 varchar,
    field8 varchar,
    field9 varchar);
"""

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

def build_ycsb(vms, env):
    parallel(lambda vm: vm.script("cd %s && mvn clean package" % YCSB_PATH), vms)

# Workload is [a..f]
def load_ycsb(vms, env, cluster, workload, record_count, operation_count):
    lock = RLock()
    insert_start = [0]
    insert_count = [record_count / len(vms)]
    op_count = [operation_count / len(vms)]

    def load_workload(vm):
        start = 0
        with lock:
            start = insert_start[0]
            insert_start[0] += insert_count[0]

        cmd = "./bin/ycsb load cassandra2-cql -P workloads/workload{3} -p hosts='{0}' -p recordcount={1} -p operationcount={2} -p insertstart={4} -p insertcount={5} -s -threads 1000 >~/load.log 2>&1"
        cmd = cmd.format(','.join(cluster.node_ip_list()), record_count, op_count[0], workload, start, insert_count[0])
        vm.script("cd {0} && {1}".format(YCSB_PATH, cmd))
    parallel(load_workload, vms)

# Workload is [a..f]
def run_ycsb(vms, env, cluster, workload, record_count, operation_count):
    lock = RLock()
    insert_start = [0]
    insert_count = [record_count / len(vms)]
    op_count = [operation_count / len(vms)]

    def run_workload(vm):
        start = 0
        with lock:
            start = insert_start[0]
            insert_start[0] += insert_count[0]

        cmd = "./bin/ycsb run cassandra2-cql -P workloads/workload{3} -p hosts='{0}' -p recordcount={1} -p operationcount={2} -p insertstart={4} -p insertcount={5} -s -threads 1000 >~/run.log 2>&1"
        cmd = cmd.format(','.join(cluster.node_ip_list()), record_count, op_count[0], workload, start, insert_count[0])
        vm.script("cd {0} && {1}".format(YCSB_PATH, cmd))

    parallel(run_workload, vms)

def ycsb_test(all_vms, env):
    benchmark_count = len(all_vms)/3
    benchmark_vms = all_vms[:benchmark_count]
    vms           = all_vms[benchmark_count:]

    parallel(lambda x: x.install('cassandra'), all_vms)
    parallel(lambda x: x.install('ycsb'), all_vms)
    parallel(lambda vm: vm.install('argos'), vms)

    setup_disks(env, vms)
    cluster = CassandraCluster(vms, benchmark_vms)
    cluster.kill()
    cluster.reset()
    cluster.setup()
    cluster.start()

    time.sleep(5)

    master = cluster.seeds[0]
    master_ip = master.intf_ip('eth0')
    master.script('sudo cat <<EOT > ~/ycsb.cql\n{0}\nEOT'.format(YcsbTemplate))
    master.script('/usr/local/cassandra/bin/cqlsh {0} -f ~/ycsb.cql '.format(master_ip))

    # Load the database
    load_ycsb(benchmark_vms, env, cluster, env.param('ycsb:workload'), int(env.param('ycsb:record_count')), int(env.param('ycsb:operation_count')))

    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

    start_time = time.time()
    run_ycsb(benchmark_vms, env, cluster, env.param('ycsb:workload'), int(env.param('ycsb:record_count')), int(env.param('ycsb:operation_count')))
    end_time = time.time()
    
    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)
    parallel(lambda vm: vm.recv('~/load.log', vm.name + '-load.out'), benchmark_vms)
    parallel(lambda vm: vm.recv('~/run.log', vm.name + '-run.out'), benchmark_vms)

    with open('vm1-time.time', 'w+') as f:
        f.write("0,{0}".format(end_time - start_time))

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, ycsb_test)
    env.benchmark.executor.run()
