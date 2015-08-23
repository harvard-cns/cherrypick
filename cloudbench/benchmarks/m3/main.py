from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.hadoop import HADOOP_USER
from cloudbench.cluster.hadoop import HadoopCluster

import re
import time

TIMEOUT=21600

TERASORT_INPUT='/home/{0}/terasort-input'.format(HADOOP_USER)
TERASORT_OUTPUT='/home/{0}/terasort-output'.format(HADOOP_USER)


def terasort_test(vms, env):
    # parallel(lambda vm: vm.install('kernel4'), vms)
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('ntp'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

    #parallel(lambda vm: vm.execute('rm -rf ~/lama/data'), vms)

    cluster = HadoopCluster(vms[0], vms[1:])
    cluster.setup()

    cluster.format_hdfs()
    cluster.restart_dfs()
    cluster.restart_yarn()

    output = cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar teragen -Dmapred.map.tasks=50 100000000 {0}"'.format(TERASORT_INPUT))
    teragen_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()

    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

    cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar terasort -Dmapred.reduce.tasks=25 {0} {1} 2>&1"'.format(TERASORT_INPUT, TERASORT_OUTPUT))
    terasort_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()

    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(10)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)

    with open(str(time.time())+'-'+cluster.master.type, 'w+') as f:
        f.write(str(teragen_time) + "," + str(terasort_time))

def run(env):
    vms = []
    for i in range(1, 4):
        vms.append(env.vm('vm'+str(i)))

    env.benchmark.executor(vms, terasort_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

