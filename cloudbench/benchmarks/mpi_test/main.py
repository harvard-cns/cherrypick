from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.cluster.base import Cluster

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

def nas_benchmark(vms, env):
    cluster = Cluster(vms, user='ubuntu')
    cluster.setup_keys()
    cluster.setup_hosts()

    parallel(lambda vm: vm.install('npb'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

    master = vms[0]
    master.script('cd npb/NPB3.3-MPI; make {0} CLASS={1} NPROCS={2}'.format(
        env.param('nas:benchmark'),
        env.param('nas:size'),
        str(master.cpus() * len(vms))
    ))

    mpi_file_name="{0}.{1}.{2}".format(
            env.param('nas:benchmark').lower(),
            env.param('nas:size').upper(),
            str(master.cpus() * len(vms)))

    parallel(lambda vm: vm.script('rm -rf npb-bins'), vms)
    parallel(lambda vm: vm.script('mkdir npb-bins'), vms)
    parallel(lambda vm: vm.script('rm npb-bins/*'), vms)

    time.sleep(2)

    master.script('cp npb/NPB3.3-MPI/bin/* npb-bins')

    # Reown everything that we lost
    parallel(lambda vm: vm.script('chown -R ubuntu:ubuntu /home/ubuntu'), vms)

    def copy_bin_files(dest):
        master.script('sudo -u ubuntu rsync -avz -e ssh /home/ubuntu/npb-bins/* ubuntu@{0}:/home/ubuntu/npb-bins >rsync-log{0}.log 2>&1'.format(dest.name))

    # Copy the mpi binary
    parallel(copy_bin_files, vms)

    hostFile = []
    for vm in vms:
        hostFile.append('{0} slots={1}'.format(vm.name, vm.cpus()))
    
    # Push the nodefile
    master.script('cat <<EOT > /home/ubuntu/npb-bins/nodefile\n{0}\nEOT'.format("\n".join(hostFile)))

    # Get ready to run the benchmark
    # Drop file caches to be more accurate for amount of reads and writes
    parallel(lambda vm: vm.script("sync; echo 3 > /proc/sys/vm/drop_caches"), vms)

    # Reown everything that we lost
    parallel(lambda vm: vm.script('chown -R ubuntu:ubuntu /home/ubuntu'), vms)

    # Start the monitoring sub-application
    monitor_start(vms)
    master.script('/usr/bin/time -f \'%e\' -o mpi.time sudo -u ubuntu mpirun -hostfile /home/ubuntu/npb-bins/nodefile /home/ubuntu/npb-bins/{0} >out.log 2>&1'.format(mpi_file_name))
    monitor_finish(vms)

    mpi_time = master.script('tail -n1 mpi.time').strip()
    mpi_out = master.script('cat out.log').strip()
    file_name = str(time.time()) + '-' + master.type
    with open(file_name + ".time", 'w+') as f:
        f.write("0," + str(mpi_time))
    with open(file_name + ".out", 'w+') as f:
        f.write(mpi_out)

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, nas_benchmark)
    env.benchmark.executor.run()
