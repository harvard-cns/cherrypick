from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

import re


TIMEOUT=300

FIO_FILENAME='/home/%s/fio.file'
FIO_FILENAME='/dev/xvdb'

def install(vm):
    vm.install('fio')

def parse_fio(result):
    """ Output of fio looks like:

    8k7030test: (g=0): rw=randrw, bs=8K-8K/8K-8K/8K-8K, ioengine=libaio, iodepth=16
    ...
    8k7030test: (g=0): rw=randrw, bs=8K-8K/8K-8K/8K-8K, ioengine=libaio, iodepth=16
    fio-2.1.3
    Starting 16 processes
    Jobs: 5 (f=5): [_____m_Em__m__mm] [9.4% done] [944KB/608KB/0KB /s] [118/76/0 iops] [eta 09m:59s]   s]
    8k7030test: (groupid=0, jobs=16): err= 0: pid=22658: Fri Jun 26 16:34:06 2015
      read : io=59168KB, bw=993295B/s, iops=121, runt= 60997msec
        slat (usec): min=2, max=1325.5K, avg=86587.43, stdev=299443.48
        clat (msec): min=24, max=3769, avg=1400.74, stdev=554.90
         lat (msec): min=24, max=4757, avg=1487.33, stdev=633.84
        clat percentiles (msec):
         |  1.00th=[   65],  5.00th=[  635], 10.00th=[ 1123], 20.00th=[ 1172],
         | 30.00th=[ 1188], 40.00th=[ 1221], 50.00th=[ 1237], 60.00th=[ 1287],
         | 70.00th=[ 1336], 80.00th=[ 1450], 90.00th=[ 2409], 95.00th=[ 2507],
         | 99.00th=[ 2638], 99.50th=[ 2704], 99.90th=[ 3523], 99.95th=[ 3556],
         | 99.99th=[ 3785]
        bw (KB  /s): min=    4, max=  249, per=6.19%, avg=60.02, stdev=19.01
      write: io=24968KB, bw=419155B/s, iops=51, runt= 60997msec
        slat (usec): min=2, max=1298.9K, avg=74661.93, stdev=276864.64
        clat (msec): min=26, max=3938, avg=1362.57, stdev=530.94
         lat (msec): min=26, max=4156, avg=1437.23, stdev=595.92
        clat percentiles (msec):
         |  1.00th=[   75],  5.00th=[ 1029], 10.00th=[ 1123], 20.00th=[ 1156],
         | 30.00th=[ 1188], 40.00th=[ 1205], 50.00th=[ 1237], 60.00th=[ 1270],
         | 70.00th=[ 1303], 80.00th=[ 1385], 90.00th=[ 2409], 95.00th=[ 2507],
         | 99.00th=[ 2802], 99.50th=[ 3228], 99.90th=[ 3752], 99.95th=[ 3949],
         | 99.99th=[ 3949]
        bw (KB  /s): min=    4, max=   90, per=6.22%, avg=25.42, stdev=12.18
        lat (msec) : 50=0.38%, 100=1.71%, 250=2.34%, 500=0.35%, 750=0.13%
        lat (msec) : 1000=0.18%, 2000=78.43%, >=2000=16.47%
      cpu          : usr=0.00%, sys=0.01%, ctx=1854, majf=0, minf=481
      IO depths    : 1=0.2%, 2=0.3%, 4=0.6%, 8=1.2%, 16=97.7%, 32=0.0%, >=64=0.0%
         submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
         complete  : 0=0.0%, 4=99.8%, 8=0.0%, 16=0.2%, 32=0.0%, 64=0.0%, >=64=0.0%
         issued    : total=r=7396/w=3121/d=0, short=r=0/w=0/d=0

    Run status group 0 (all jobs):
       READ: io=59168KB, aggrb=970KB/s, minb=970KB/s, maxb=970KB/s, mint=60997msec, maxt=60997msec
      WRITE: io=24968KB, aggrb=409KB/s, minb=409KB/s, maxb=409KB/s, mint=60997msec, maxt=60997msec

    Disk stats (read/write):
      sda: ios=7392/3124, merge=0/1, ticks=5809952/2314148, in_queue=8131284, util=99.90%

    """
    out = {}
    for line in result.split("\n"):
        if 'READ' in line:
            reg = re.search('aggrb=(.*?)/s', line)
            if reg: out['read'] = reg.group(1)

        if 'WRITE' in line:
            reg = re.search('aggrb=(.*?)/s', line)
            if reg: out['write'] = reg.group(1)

    return out

def _fio_r100_w0(vm):
    filename = FIO_FILENAME
    #filename = FIO_FILENAME % vm.username

    vm.execute('sudo killall fio')
    vm.execute('sudo rm -rf {0}'.format(filename))
    output = vm.execute('sudo fio --filename={0} --direct=1 \
--rw=randrw --refill_buffers --norandommap --randrepeat=0 --ioengine=libaio \
--bs=4k --size={1} --rwmixread=100 --iodepth=16 --numjobs=16 --size={1} --runtime=60 \
--group_reporting --name=4ktest'.format(filename, 1024*1024*1024))
    return parse_fio(output)

def _fio_r70_w30(vm):
    filename = FIO_FILENAME
    #filename = FIO_FILENAME % vm.username

    vm.execute('sudo killall fio')
    vm.execute('sudo rm -rf {0}'.format(filename))
    output = vm.execute('sudo fio --filename={0} --direct=1 \
--rw=randrw --refill_buffers --norandommap --randrepeat=0 --ioengine=libaio \
--bs=8k --size={1} --rwmixread=70 --iodepth=16 --numjobs=16 --size={1} --runtime=60 \
--group_reporting --name=8k7030test'.format(filename, 1024*1024*1024))
    return parse_fio(output)

def fio(vm, env):
    output = {}
    output['server_location'] = vm.location().location

    t = _fio_r70_w30(vm)
    if 'read' in t:
        output['r70'] = t['read']
    if 'write' in t:
        output['w30'] = t['write']
    t = _fio_r100_w0(vm)
    if 'read' in t:
        output['r100'] = t['read']

    return output


def bonnie(vm):
    return vm

def fio_test(vms, env):
    vm = vms[0]
    install(vm)
    results = fio(vm, env)
    print results


def run(env):
    vm1 = env.vm('vm-east')

    env.benchmark.executor([vm1], fio_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

