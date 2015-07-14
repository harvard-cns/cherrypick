from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

import re


TIMEOUT=300

COREMARK_PATH='~/coremark'
COREMARK_FILE='coremark_v1.0.tgz'
COREMARK_DIR='coremark_v1.0'
COREMARK_REMOTE_PATH='~/coremark/{0}'.format(COREMARK_DIR)

def install_coremark(vm):
    vm.ssh() << WaitUntilFinished('sudo apt-get update -y')
    vm.ssh() << WaitUntilFinished('sudo apt-get install build-essential -y')
    vm.ssh() << WaitUntilFinished("mkdir -p {0}".format(COREMARK_PATH))
    rsync = vm.rsync()
    rsync.send("../tools/{0}".format(COREMARK_FILE), COREMARK_PATH)
    output = rsync.wait()

def parse_coremark(vm):
    ssh = vm.ssh(new=True)
    ssh << WaitUntilFinished("\"cd %s && cat run1.log | grep 'Iterations/Sec' | awk '{print $3}'\"" % COREMARK_REMOTE_PATH)

    output = {}
    output['server_location'] = vm.location().location
    output['coremark'] = ssh.read().strip()

    return output



def coremark(vm, env):
    output = {}

    vm.ssh() << WaitUntilFinished("'cd {0} && tar zxf {1}'".format(COREMARK_PATH, COREMARK_FILE))

    # Warmup
    vm.ssh() << WaitUntilFinished("'cd {0} && make'".format(COREMARK_REMOTE_PATH))

    # Execution
    vm.ssh() << WaitUntilFinished("'cd {0} && make'".format(COREMARK_REMOTE_PATH))

    return parse_coremark(vm)

def coremark_test(vms, env):
    vm = vms[0]
    install_coremark(vm)
    results = coremark(vm, env)
    print results

def run(env):
    vm1 = env.vm('vm-coremark')

    env.benchmark.executor([vm1], coremark_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

