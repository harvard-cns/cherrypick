from cloudbench.ssh import WaitUntilFinished
from cloudbench.util import Debug

import re

def _extract_rtts(hping_result):
    rtts = []
    for line in hping_result.split("\n"):
        if 'rtt' not in line:
            continue

        rtt = re.findall('rtt=([-+]?[0-9]*\.?[0-9]+)', line)
        if (len(rtt) > 0):
            rtts.append(float(rtt[0]))

    rtts.sort()
    return rtts

def _hping_ip(vm1, vm2, vm2_address):
    rtts = []

    while not(rtts):
        vm1_ssh = vm1.ssh(new=True)
        vm1_ssh_warmup = vm1.ssh(new=True)
        query = 'sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm2_address
        warmup = 'sudo hping3 -c 5 -S -I eth0 -p 22 ' + vm2_address

        # Run a warmup
        for _ in range(3):
            vm1_ssh_warmup << WaitUntilFinished(warmup)

        vm1_ssh_warmup.terminate()

        vm1_ssh << WaitUntilFinished(query)
        vm1_ssh.terminate()

        rtts = _extract_rtts(vm1_ssh.read())

    out = {
        'server_location': vm2.location().location, # The VM the answered the ping
        'client_location': vm1.location().location, # The VM that initiated the ping
        'rtt_avg': sum(rtts)/len(rtts),
        'rtt_0': rtts[0],
        'rtt_10': rtts[1],
        'rtt_50': rtts[len(rtts)/2],
        'rtt_90': rtts[-2],
        'rtt_100': rtts[-1]
    }

    return out

def hping(vm1, vm2, env):
    return _hping_ip(vm1, vm2, vm2.url)

def hping_vnet(vm1, vm2, env):
    vm2_ssh = vm1.ssh(new=True)
    vm2_ssh << WaitUntilFinished("hostname -I")
    vm2_ip = vm2_ssh.read()

    return _hping_ip(vm1, vm2, vm2_ip)

def run(env):
    vm_east = env.vm('vm-east')
    vm_west = env.vm('vm-west')

    Debug << 'Installing hping3\n'
    vm_east.ssh() << WaitUntilFinished('sudo apt-get install hping3 -y')
    vm_west.ssh() << WaitUntilFinished('sudo apt-get install hping3 -y')

    output = hping(vm_east, vm_west, env)
    print output
