from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera

import re
import time

TIMEOUT=21600

def monitor_start(vms):
    # Start IO monitor
    # parallel(lambda vm: vm.monitor(), vms)

    # Start Argos
    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

def monitor_finish(vms):
    # Save IO monitor
    # parallel(lambda vm: vm.stop_monitor(), vms)
    # parallel(lambda vm: vm.download_monitor(vm.name + '-disk-usage.log'), vms)

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

def setup_base(env, vms):
    setup_disks(env, vms)
    parallel(lambda vm: vm.install('java8'), vms)
    parallel(lambda vm: vm.install('cloudera'), vms)
    parallel(lambda vm: vm.install('git'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

def terasort(vms, env):
    hadoop = setup_hadoop(env, vms)
    print "Master is: %s" % hadoop.master.name

    hadoop.execute('sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5*.jar teragen -D mapred.map.tasks={0} {1} /terasort-input'.format(env.param('terasort:mappers'), env.param('terasort:rows')))

    monitor_start(vms)
    hadoop.execute('/usr/bin/time -f \'%e\' -o terasort.out sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5*.jar terasort -D mapred.reduce.tasks={0} /terasort-input /terasort-output >output.log 2>&1'.format(env.param('terasort:reducers')))
    monitor_finish(vms)

    terasort_time = hadoop.master.script('tail -n1 terasort.out').strip()
    terasort_out = hadoop.master.script('cat output.log').strip()
    file_name = str(time.time()) + '-' + hadoop.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write("0," + str(terasort_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(terasort_out)

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, terasort)
    env.benchmark.executor.run()
