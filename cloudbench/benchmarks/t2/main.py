from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.hadoop import HADOOP_USER
from cloudbench.cluster.hadoop import HadoopCluster
from cloudbench.benchmarks.terasort import terasort_run

import re
import time

TIMEOUT=21600

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, terasort_run)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

