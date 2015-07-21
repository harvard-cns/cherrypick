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
        query = 'sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm2_address
        warmup = 'sudo hping3 -c 5 -S -I eth0 -p 22 ' + vm2_address

        # Run a warmup
        for _ in range(1):
            vm1.execute(warmup)

        rtts = _extract_rtts(vm1.execute(query))

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
    vm2_ip = vm2.execute('hostname -I').strip()
    return _hping_ip(vm1, vm2, vm2_ip)

def run(env):
    vm_east = env.vm('vm-east')
    vm_west = env.vm('vm-west')

    Debug << 'Installing hping3\n'
    vm_east.install('hping3')
    vm_west.install('hping3')

    output = hping(vm_east, vm_west, env)
    print output
