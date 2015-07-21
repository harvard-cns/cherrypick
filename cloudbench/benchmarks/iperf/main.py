from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
import time


TIMEOUT=300

def _iperf(vm1, vm2, vm1_address):
    vm1_ssh = vm1.ssh(new=True)
    vm2_ssh = vm2.ssh(new=True)
    vm2_ssh_warmup = vm2.ssh(new=True)

    while True:
        Debug << "Running iperf client and server.\n"
        vm1.execute('sudo killall -9 iperf')
        vm1.execute('iperf -s -y C', daemon=True)
        time.sleep(3)

        Debug << "Warming up ..."
        for _ in range(1):
            vm2.execute('iperf -y C -c ' + vm1_address)

        Debug << "Measuring iperf"
        output = vm2.execute('iperf -y C -c ' + vm1_address)

        if not output:
            continue

        vm1.execute('sudo killall -9 iperf')

        res = output.strip().split(",")
        out = {
            'server_location': vm1.location().location,
            'server_ip': res[1],
            'server_port': res[2],
            'client_location': vm2.location().location,
            'client_ip': res[3],
            'client_port': res[4],
            'bandwidth': res[8]
        }

        return out


def iperf(vm1, vm2, env):
    return _iperf(vm1, vm2, vm1.url)

def iperf_vnet(vm1, vm2, env):
    vm1_address = vm1.execute('hostname -I')
    return _iperf(vm1, vm2, vm1_address)

def exec_iperf(vms, env):
    vm1, vm2 = vms

    Debug << "Installing iperf.\n"
    vm1.install('iperf')
    vm2.install('iperf')

    print iperf(vm1, vm2, env)


def run(env):
    vm1 = env.vm('vm-east')
    vm2 = env.vm('vm-west')

    env.benchmark.executor([vm1, vm2], exec_iperf, 'iperf')
    env.benchmark.executor.run()
