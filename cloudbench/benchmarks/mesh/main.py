from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from multiprocessing.pool import ThreadPool

import re
import traceback, sys

# Timeout of 50 minutes
TIMEOUT=50*60

def unixify(name):
    return name.lower().replace(' ', '_')

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

    env.storage().save(out, partition='iperfmesh', key=(unixify(server) 
        + '_' + unixify(client)))

def save_hping(env, rtts, server, client):
    out = {
        'server_location': server,
        'client_location': client,
        'rtt_avg': sum(rtts)/len(rtts),
        'rtt_0': rtts[0],
        'rtt_10': rtts[1],
        'rtt_50': rtts[len(rtts)/2],
        'rtt_90': rtts[-2],
        'rtt_100': rtts[-1]
    }

    env.storage().save(out, partition='hpingmesh', key=(unixify(server) 
        + '_' + unixify(client)))

def _iperf(vm1, vm2, env):
    vm1_ssh = vm1.ssh(new=True)
    vm2_ssh = vm2.ssh(new=True)
    vm2_ssh_warmup = vm2.ssh(new=True)

    while True:
        Debug << "Running iperf client and server.\n"
        vm1_ssh << WaitUntilFinished("sudo killall -9 iperf")
        vm1_ssh << WaitForSeconds('iperf -s -y C', 3)

        Debug << "Warming up ..."
        vm2_ssh_warmup << WaitUntilFinished('iperf -y C -c ' + vm1.url)
        vm2_ssh_warmup << WaitUntilFinished('iperf -y C -c ' + vm1.url)
        vm2_ssh_warmup << WaitUntilFinished('iperf -y C -c ' + vm1.url)
        vm2_ssh_warmup.terminate()

        Debug << "Measuring iperf"
        vm2_ssh << WaitUntilFinished('iperf -y C -c ' + vm1.url)
        output = vm2_ssh.read()

        if not output:
            continue

        Debug.cmd << output
        save_iperf(env, output, vm1.location().location, vm2.location().location)

        vm1_ssh.terminate()
        vm2_ssh.terminate()
        return

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
    vm1_ssh = vm1.ssh(new=True)
    vm1_ssh_warmup = vm1.ssh(new=True)

    query = 'sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm2.url
    warmup = 'sudo hping3 -c 5 -S -I eth0 -p 22 ' + vm2.url

    vm1_ssh_warmup << WaitUntilFinished(warmup)
    vm1_ssh_warmup << WaitUntilFinished(warmup)
    vm1_ssh_warmup << WaitUntilFinished(warmup)

    vm1_ssh_warmup.terminate()

    vm1_ssh << WaitUntilFinished(query)
    vm1_ssh.terminate()

    rtts = _extract_rtts(vm1_ssh.read())
    save_hping(env, rtts, vm2.location().location, vm1.location().location)

# Iperf both sides
def experiment(params):
    vm1, vm2, env = params[0], params[1], params[2]
    try:
        _iperf(vm1, vm2, env)
        _hping(vm1, vm2, env)
    except:
        print "Exception in user code:"
        print '-' * 60
        traceback.print_exc(file=sys.stdout)
        print '-' * 60
        exit()

def run(env):
    regions = {}

    # Categorize VMs based on their location
    for _, vm in env.virtual_machines().iteritems():
        group_name = vm.location().name
        if group_name not in regions:
            regions[group_name] = []
        regions[group_name].append(vm)


    def install(vm):
        vm.ssh() << WaitUntilFinished("sudo apt-get install hping3 -y")
        vm.ssh() << WaitUntilFinished("sudo apt-get install iperf -y")

    pool = ThreadPool(len(env.virtual_machines().values()))
    pool.map(install, env.virtual_machines().values())

    # Inter-location iperf/hping
    for key1 in regions:
        jobs = []
        for key2 in regions:
            if (key1 != key2):
                jobs.append((regions[key2][0], regions[key1][0], env,))
                
        pool = ThreadPool(len(env.locations())-1)
        pool.map(experiment, jobs)


    # Intra-location iperf/hping
    jobs = []
    for key1 in regions:
        jobs.append((regions[key1][0], regions[key1][1], env,))

    pool = ThreadPool(len(env.groups()))
    pool.map(experiment, jobs)
