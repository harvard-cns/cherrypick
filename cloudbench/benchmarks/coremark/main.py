from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from cloudbench.apps.coremark import COREMARK_PATH, COREMARK_FILE, COREMARK_REMOTE_PATH

import re


TIMEOUT=3600

def coremark(vm, env):
    output = {}

    # Warmup
    vm.execute("'cd {0} && make REBUILD=1'".format(COREMARK_REMOTE_PATH))

    # Execution
    vm.execute("'cd {0} && make REBUILD=1'".format(COREMARK_REMOTE_PATH))

    out = vm.execute("\"cd %s && cat run1.log | grep 'Iterations/Sec' | awk '{print $3}'\"" % COREMARK_REMOTE_PATH)

    output = {}
    output['server_location'] = vm.location().location
    output['coremark'] = out.strip()

    return output

def coremark_mp(vm, env):
    output = {}

    # Warmup
    vm.execute("'cd {0} && make REBUILD=1 XCFLAGS=\"-DMULTITHREAD={1} -pthread -DUSE_PTHREAD\"'".format(COREMARK_REMOTE_PATH, vm.cpus()))

    # Execution
    vm.execute("'cd {0} && make REBUILD=1 XCFLAGS=\"-DMULTITHREAD={1} -pthread -DUSE_PTHREAD\"'".format(COREMARK_REMOTE_PATH, vm.cpus()))

    out = vm.execute("\"cd %s && cat run1.log | grep 'Iterations/Sec' | awk '{print $3}'\"" % COREMARK_REMOTE_PATH)

    output = {}
    output['server_location'] = vm.location().location
    output['coremark_mp'] = out.strip()

    return output

def coremark_test(vms, env):
    vm = vms[0]

    # Install the new kernel
    #vm.install('kernel4')
    vm.install('coremark')

    results = coremark(vm, env)
    print results
    results = coremark_mp(vm, env)
    print results

def run(env):
    vm1 = env.vm('vm-coremark')

    env.benchmark.executor([vm1], coremark_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

