from cloudbench.ssh import WaitUntilFinished
from cloudbench.util import Debug

def run(env):
    vm_east = env.vm('vm-east').ssh()
    vm_west = env.vm('vm-west').ssh()

    Debug << 'Installing hping3\n'
    vm_east << WaitUntilFinished('sudo apt-get install hping3 -y')
    vm_west << WaitUntilFinished('sudo apt-get install hping3 -y')

    Debug << 'Getting the public IP\n'
    vm_east_ip = vm_east.ip()
    vm_west_ip = vm_west.ip()

    Debug << "East IP: " << vm_east_ip << '\n'
    Debug << "West IP: " << vm_west_ip << '\n'

    vm_west << WaitUntilFinished('sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm_east_ip)
    vm_west.terminate()

    Debug << "West to east\n"
    print vm_west.read()

    vm_east << WaitUntilFinished('sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm_west_ip)
    vm_east.terminate()

    Debug << "East to west\n"
    print vm_east.read()

    vm_east.read()
    vm_west.read()
