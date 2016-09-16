from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cloudera.cloudera import Cloudera

import os
import re
import time

TIMEOUT=21600

def makedirectory(name):
    if not os.path.exists(name):
        os.makedirs(name)

def monitor_start(vms):
    # Start IO monitor
    # parallel(lambda vm: vm.monitor(), vms)

    # Start Argos
    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

def monitor_finish(vms, directory, iteration):
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

    subdir=os.path.join(directory, str(iteration))
    makedirectory(subdir)

    # Save argos results
    parallel(lambda vm: vm.recv('~/argos/proc', os.path.join(subdir, vm.name + '-proc')), vms)

    # Save argos output
    parallel(lambda vm: vm.recv('~/argos/argos.out', os.path.join(subdir, vm.name + '-argos.out')), vms)


def setup_hadoop(env, vms):
    setup_base(env, vms)
    ce = Cloudera(vms)
    ce.install('Hadoop')
    return ce['Hadoop']

def setup_disks(env, vms):
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

def setup_base(env, vms):
    setup_disks(env, vms)
    parallel(lambda vm: vm.install('java8'), vms)
    parallel(lambda vm: vm.install('cloudera'), vms)
    parallel(lambda vm: vm.install('git'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

def terasort(vms, env):
    hadoop = setup_hadoop(env, vms)
    print "Master is: %s" % hadoop.master.name

    directory='terasort-' + hadoop.master.type + '-' + str(len(vms)) + "-results"
    makedirectory(directory)
    iteration=str(1)

    extra_teragen_params = "-Ddfs.blocksize=512M -Dmapreduce.task.io.sort.mb=256"

    hadoop.master.execute("sudo service hadoop-hdfs-namenode restart")
    hadoop.master.execute("sudo service hadoop-hdfs-datanode restart")
    hadoop.master.execute("sudo service hadoop-yarn-resourcemanager restart")

    mapper_count = int(4 * int(sum(map(lambda vm: vm.cpus(), vms))) * 0.8)
    hadoop.execute('sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5*.jar teragen {2} -D mapred.map.tasks={0} {1} /terasort-input'.format(mapper_count, env.param('terasort:rows'), extra_teragen_params))

    # Drop file caches to be more accurate for amount of reads and writes
    parallel(lambda vm: vm.script("sync; echo 3 > /proc/sys/vm/drop_caches"), vms)

    reducer_count = int(sum(map(lambda vm: vm.cpus(), vms)) * 0.8)

    extra_terasort_params = "-Ddfs.blocksize=512M -Dmapreduce.task.io.sort.factor=100 -Dmapreduce.task.io.sort.mb=384 -Dio.file.buffer.size=131072"
    monitor_start(vms)
    hadoop.execute('/usr/bin/time -f \'%e\' -o terasort.out sudo -u hdfs hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples-2.6.0-mr1-cdh5*.jar terasort {1} -D mapred.reduce.tasks={0} /terasort-input /terasort-output >output.log 2>&1'.format(str(reducer_count), extra_terasort_params))
    monitor_finish(vms, directory, iteration)

    terasort_time = hadoop.master.script('tail -n1 terasort.out').strip()
    terasort_out = hadoop.master.script('cat output.log').strip()
    file_name = hadoop.master.type
    with open(os.path.join(directory, str(iteration), file_name + ".time"), 'w+') as f:
        f.write("0," + str(terasort_time))

    with open(os.path.join(directory, str(iteration), file_name + ".out"), 'w+') as f:
        f.write(terasort_out)

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, terasort)
    env.benchmark.executor.run()
