from cloudbench.ssh import WaitUntilFinished

def run(env):
    vm_east = env.vm('vm-east').ssh()
    vm_west = env.vm('vm-west').ssh()

    print 'Installing hping3'
    vm_east << WaitUntilFinished('sudo apt-get install hping3 -y')
    vm_west << WaitUntilFinished('sudo apt-get install hping3 -y')

    print 'Getting the public IP'
    vm_east_ip = vm_east.ip()
    vm_west_ip = vm_west.ip()

    print "East IP: %s" % vm_east_ip
    print "West IP: %s" % vm_west_ip

    vm_west << WaitUntilFinished('sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm_east_ip)
    vm_west.terminate()

    print "West to east"
    print vm_west.read()

    vm_east << WaitUntilFinished('sudo hping3 -c 20 -S -I eth0 -p 22 ' + vm_west_ip)
    vm_east.terminate()

    print "East to west"
    print vm_east.read()

    vm_east.read()
    vm_west.read()
