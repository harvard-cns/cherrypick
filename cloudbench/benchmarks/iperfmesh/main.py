from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

import re

def save_iperf(env, results, server, client):
    res = results.strip().split(",")
    out = {
        'timestamp': res[0],
        'server_location': server,
        'server_ip': res[1],
        'server_port': res[2],
        'client_location': client,
        'client_ip': res[3],
        'client_port': res[4],
        'bandwidth': res[8]
    }
    print out

    env.storage().save(out, key='iperfmesh')

def save_hping(env, rtts, server, client):
    out = {
        'server_location': server,
        'client_location': client,
        'rtt_avg': sum(rtts)/len(rtts),
        'rtt_0': rtts[0],
        'rtt_10': rtts[1],
        'rtt_50': rtts[9],
        'rtt_90': rtts[18],
        'rtt_100': rtts[19]
    }

    print out

    env.storage().save(out, key='hpingmesh')

def _iperf(vm1, vm2, env):
    vm1_ip = vm1.ssh().ip()
    Debug << vm1_ip << "\n"

    Debug << "Running iperf client and server.\n"
    vm1.ssh() << WaitUntilFinished("killall -9 iperf")
    vm1.ssh() << WaitForSeconds('iperf -s -y C', 3)
    vm2.ssh() << WaitUntilFinished('iperf -y C -c ' + vm1_ip)

    output = vm2.ssh().read()
    Debug.cmd << output
    save_iperf(env, output, vm1.group().location(),
            vm2.group().location())

    vm1.ssh().terminate()
    vm2.ssh().terminate()

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

def _hping(vm1, vm2, env):
    vm1_ip = vm1.ssh().ip()
    vm2_ip = vm2.ssh().ip()
    Debug << vm1_ip << "\n"

    vm1.ssh() << WaitUntilFinished('sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm1_ip)
    vm1.ssh().terminate()
    rtts = _extract_rtts(vm1.ssh().read())
    save_hping(env, rtts, vm1.group().location(), vm2.group().location())

    vm2.ssh() << WaitUntilFinished('sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm2_ip)
    vm2.ssh().terminate()
    rtts = _extract_rtts(vm2.ssh().read())
    save_hping(env, rtts, vm2.group().location(), vm1.group().location())

# Iperf both sides
def experiment(vm1, vm2, env):
    _hping(vm1, vm2, env)
    _hping(vm2, vm1, env)
    _iperf(vm1, vm2, env)
    _iperf(vm2, vm1, env)

def run(env):
    regions = {}

    for vm in env.virtual_machines():
        group_name = vm.group().name
        if group_name not in regions:
            regions[group_name] = []

        # vm.ssh() << WaitUntilFinished("sudo apt-get install hping3 -y")
        # vm.ssh() << WaitUntilFinished("sudo apt-get install iperf -y")
        regions[group_name].append(vm)

    for key1 in regions:
        for key2 in regions:
            # Intra-region iperf
            if (key1 == key2):
                experiment(regions[key1][0], regions[key1][1], env)
            else:
                experiment(regions[key1][0], regions[key2][0], env)


