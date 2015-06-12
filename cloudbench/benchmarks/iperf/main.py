from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

def run(env):
    vm1 = env.vm('vm1').ssh()
    vm2 = env.vm('vm2').ssh()

    vm1_ip = vm1.ip()
    Debug << vm1_ip << "\n"

    Debug << "Installing iperf.\n"
    vm1 << WaitUntilFinished('sudo apt-get install iperf -y')
    vm2 << WaitUntilFinished('sudo apt-get install iperf -y')

    Debug << "Running iperf client and server.\n"
    vm1 << WaitUntilFinished("killall -9 iperf")
    vm1 << WaitForSeconds('iperf -s -y C', 3)
    vm2 << WaitUntilFinished('iperf -y C -c ' + vm1_ip)

    print vm2.read()
    vm1.terminate()
    vm2.terminate()
