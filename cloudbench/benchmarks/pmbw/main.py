from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

import re


TIMEOUT=300

PMBW_PATH='~/pmbw'
PMBW_FILE='pmbw-0.6.2.tar.bz2'
PMBW_DIR='pmbw-0.6.2'
PMBW_REMOTE_PATH='{0}/{1}'.format(PMBW_PATH, PMBW_DIR)

def install_pmbw(vm):
    vm.ssh() << WaitUntilFinished('sudo apt-get update -y')
    vm.ssh() << WaitUntilFinished('sudo apt-get install build-essential -y')
    vm.ssh() << WaitUntilFinished("'mkdir -p {0}'".format(PMBW_PATH))
    rsync = vm.rsync()
    rsync.send("../tools/{0}".format(PMBW_FILE), PMBW_PATH)
    output = rsync.wait()

def extract_funcname(line):
    for part in filter(lambda x: x, re.split('\s+', line)):
        if part.split("=")[0].strip() == 'funcname':
            return part.split("=")[1].strip()
    return None

def extract_bandwidth(line):
    for part in filter(lambda x: x, re.split('\s+', line)):
        if part.split("=")[0].strip() == 'bandwidth':
            return float(part.split("=")[1].strip())
    return None

def parse_pmbw(out):
    output = {}

    for l in out.split("\n"):
        l = l.strip()
        if not l:
            continue
        func = extract_funcname(l)
        bandwidth = extract_bandwidth(l)
        if func and bandwidth:
            output[func] = bandwidth

    return output



def pmbw(vm, env):
    vm.ssh() << WaitUntilFinished("'cd {0} && tar xjf {1}'".format(PMBW_PATH, PMBW_FILE))

    # Build PMBW
    vm.ssh() << WaitUntilFinished("'cd {0} && ./configure && make'".format(PMBW_REMOTE_PATH))

    # Execution
    ssh = vm.ssh(new=True)
    ssh << WaitUntilFinished("'cd %s && ./pmbw -p 1 -P 1 2>/dev/null'" % (PMBW_REMOTE_PATH,))
    output = parse_pmbw(ssh.read())
    output['server_location'] = vm.location().location
    return output

def pmbw_test(vms, env):
    vm = vms[0]
    install_pmbw(vm)
    print pmbw(vm, env)

def run(env):
    vm1 = env.vm('vm-pmbw')

    env.benchmark.executor([vm1], pmbw_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

