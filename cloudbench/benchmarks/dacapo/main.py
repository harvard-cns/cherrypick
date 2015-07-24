from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

import re

TIMEOUT=30000000

def dacapo_for_vm(vm):
    vm.install('dacapo')
    print vm.script('date')


def dacapo_test(vms, env):
    parallel(dacapo_for_vm, vms)

def run(env):
    vms = []
    for i in range(0, 5):
        vms.append(env.vm('vm-dacapo' + str(i)))

    env.benchmark.executor(vms, dacapo_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

