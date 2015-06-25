from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug


TIMEOUT=300

def save(env, results):
    res = results.strip().split(",")
    out = {
        'timestamp': res[0],
        'server_ip': res[1],
        'server_port': res[2],
        'client_ip': res[3],
        'client_port': res[4],
        'bandwidth': res[8]
    }

    env.storage().save(out)

def run(env):
    vm1 = env.vm('vm-east').ssh()
    vm2 = env.vm('vm-west').ssh()

    Debug << "Installing iperf.\n"
    vm1 << WaitUntilFinished('sudo apt-get install iperf -y')
    vm2 << WaitUntilFinished('sudo apt-get install iperf -y')

    Debug << "Running iperf client and server.\n"
    vm1 << WaitUntilFinished("killall -9 iperf")
    vm1 << WaitForSeconds('iperf -s -y C', 3)
    vm2 << WaitUntilFinished('iperf -y C -c ' + vm1.vm().url)

    output = vm2.read()
    Debug.cmd << output
    #save(env, output)

    vm1.terminate()
    vm2.terminate()
