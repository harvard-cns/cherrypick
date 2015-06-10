#
#   fio --filename=/dev/sdx --direct=1 --rw=randrw --refill_buffers
#   --norandommap --randrepeat=0 --ioengine=libaio --bs=8k --rwmixread=70
#   --iodepth=16 --numjobs=16 --runtime=60 --group_reporting
#   --name=8k7030test

from ssh import WaitUntilFinished, WaitForSeconds

def run(env):
    vm_east = env.vm('vm-east').ssh()
    vm_west = env.vm('vm-west').ssh()

    vm_east << WaitUntilFinished('sudo apt-get install hping3 -y')
    vm_west << WaitUntilFinished('sudo apt-get install hping3 -y')

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
