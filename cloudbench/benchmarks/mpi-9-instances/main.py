from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel
from cloudbench.benchmarks.mpi_test import nas_benchmark

import re
import time

TIMEOUT=21600

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, nas_benchmark)
    env.benchmark.executor.run()
