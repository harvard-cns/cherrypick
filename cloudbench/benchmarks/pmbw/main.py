from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

from cloudbench.apps.pmbw import PMBW_PATH, PMBW_FILE, PMBW_REMOTE_PATH

import re

TIMEOUT=300

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
    # Build PMBW
    vm.execute("'cd {0} && ./configure && make'".format(PMBW_REMOTE_PATH))

    # Execution
    ssh = vm.ssh(new=True)
    ssh << WaitUntilFinished("'cd %s && ./pmbw -p 1 -P 1 2>/dev/null'" % (PMBW_REMOTE_PATH,))
    output = parse_pmbw(ssh.read())
    output['server_location'] = vm.location().location
    return output

def pmbw_test(vms, env):
    vm = vms[0]
    vm.install('pmbw')
    print pmbw(vm, env)

def run(env):
    vm1 = env.vm('vm-pmbw')

    env.benchmark.executor([vm1], pmbw_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

