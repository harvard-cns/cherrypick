from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug


TIMEOUT=300

def _iperf(vm1, vm2, vm1_address):
    vm1_ssh = vm1.ssh(new=True)
    vm2_ssh = vm2.ssh(new=True)
    vm2_ssh_warmup = vm2.ssh(new=True)

    while True:
        Debug << "Running iperf client and server.\n"
        vm1_ssh << WaitUntilFinished("sudo killall -9 iperf")
        vm1_ssh << WaitForSeconds('iperf -s -y C', 3)

        Debug << "Warming up ..."
        for _ in range(1):
            vm2_ssh_warmup << WaitUntilFinished('iperf -y C -c ' + vm1_address)
        vm2_ssh_warmup.terminate()

        Debug << "Measuring iperf"
        vm2_ssh << WaitUntilFinished('iperf -y C -c ' + vm1_address)
        output = vm2_ssh.read()

        if not output:
            continue

        vm1_ssh.terminate()
        vm2_ssh.terminate()

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
    vm1_ssh = vm1.ssh(new=True)
    vm1_ssh << WaitUntilFinished("hostname -I")
    vm1_address = vm1_ssh.read()

    return _iperf(vm1, vm2, vm1_address)

def run(env):
    vm1 = env.vm('vm-east')
    vm2 = env.vm('vm-west')

    Debug << "Installing iperf.\n"
    vm1.ssh() << WaitUntilFinished('sudo apt-get install iperf -y')
    vm2.ssh() << WaitUntilFinished('sudo apt-get install iperf -y')

    print iperf(vm1, vm2, env)

    vm1.terminate()
    vm2.terminate()
