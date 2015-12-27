from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from multiprocessing.pool import ThreadPool

from cloudbench.benchmarks.io.main import fio
from cloudbench.benchmarks.pmbw.main import pmbw
from cloudbench.benchmarks.hdparm.main import hdparm
from cloudbench.benchmarks.coremark.main import coremark, coremark_mp
from cloudbench.storage import JsonStorage

import json
import re
import traceback, sys

from threading import RLock

# Timeout of 50 minutes
TIMEOUT=50*60
BLOCKCOUNT=4
BLOCKSIZE=256
MBCOUNT=BLOCKSIZE * BLOCKCOUNT * 1000000/(1024*1024.0)

def install(vm):
    vm.script('sudo aptitude update')
    vm.install('parallel')
    vm.install('coremark')

def disk_script(vm):
    disks = vm.all_disks_except_root()

    ebs_disks = filter(lambda x: not x.endswith(('b', 'c', 'd', 'e')), disks)
    local_disks = filter(lambda x: x.endswith(('b', 'c', 'd', 'e')), disks)

    print "Ebs disks:", ebs_disks
    print "Local disks:", local_disks

    read  = 'sudo dd if=%s of=/dev/null bs=%dMB count=%d' % ('%s', BLOCKSIZE, BLOCKCOUNT)
    write = 'sudo dd if=/dev/zero of=%s bs=%dMB count=%d conv=fdatasync' % ('%s', BLOCKSIZE, BLOCKCOUNT)

    print "Command: %s" % read

    def run_benchmark(commands, disks):
        script = "\n".join([cmd % disk for cmd in commands for disk in disks])
        command = "sudo cat <<EOT > script.txt\n{0}\nEOT".format(script)
        vm.script(command)
        vm.script('/usr/bin/time -f \'%e\' -o time.out parallel < script.txt')
        print vm.script('cat time.out')
        timeLen = float(vm.script('cat time.out'))
        return len(commands) * len(disks) * MBCOUNT /  timeLen

    output = {}
    if len(ebs_disks) > 0:
        output['ebs-single-r']  = run_benchmark([read] , [ebs_disks[0]])
        output['ebs-single-w']  = run_benchmark([write], [ebs_disks[0]])
        output['ebs-single-rw'] = run_benchmark([read, write], [ebs_disks[0]])

    if len(ebs_disks) > 1:
        output['ebs-multi-r']  = run_benchmark([read] , ebs_disks)
        output['ebs-multi-w']  = run_benchmark([write], ebs_disks)
        output['ebs-multi-rw'] = run_benchmark([read, write], ebs_disks)

    if len(local_disks) > 0:
        output['local-single-r']  = run_benchmark([read] , [local_disks[0]])
        output['local-single-w']  = run_benchmark([write], [local_disks[0]])
        output['local-single-rw'] = run_benchmark([read, write], [local_disks[0]])

    if len(local_disks) > 1:
        output['local-multi-r']  = run_benchmark([read] , local_disks)
        output['local-multi-w']  = run_benchmark([write], local_disks)
        output['local-multi-rw'] = run_benchmark([read, write], local_disks)

    return output

def cpu_script(vm, env):
    coremp = coremark_mp(vm, env)
    coresp = coremark(vm, env)

    return {'coremp': coremp, 'coresp': coresp}

def run_benchmarks(vms, env):
    vm = vms[0]
    install(vm)

    for iteration in range(1, 3):
        res = {}
        res.update(disk_script(vm))
        res.update(cpu_script(vm, env))

        storage = JsonStorage(env, vm.type + '-' + str(iteration) + '-' + 'local' + '.json')
        storage.save(res)
        print ('Result: %s' % res)

def run(env):
    """ Run the mesh benchmark.
    
    Three different categories of experiments

    1) Intra data-center pairwise expeirments
    2) Inter data-center pairwise experiments
    3) Single VM experiments

    """
    vm = env.virtual_machines().values()[0]
    env.benchmark.executor([vm], run_benchmarks, '')
    env.benchmark.executor.run()
