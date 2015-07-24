from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.hadoop import HADOOP_USER
from cloudbench.cluster.hadoop import HadoopCluster

import re

TIMEOUT=360000

TERASORT_INPUT='/home/{0}/terasort-input'.format(HADOOP_USER)
TERASORT_OUTPUT='/home/{0}/terasort-output'.format(HADOOP_USER)


def terasort_test(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)

    cluster = HadoopCluster(vms[0], vms[1:])
    cluster.setup()

    cluster.format_hdfs()
    cluster.restart_dfs()
    cluster.restart_yarn()

    out = cluster.execute('"hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar teragen 100000000 {0}"'.format(TERASORT_INPUT))
    out = cluster.execute('"time hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar terasort {0} {1}"'.format(TERASORT_INPUT, TERASORT_OUTPUT))
    print out

def run(env):
    vms = []
    for i in range(1, 6):
        vms.append(env.vm('vm'+str(i)))

    env.benchmark.executor(vms, terasort_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

