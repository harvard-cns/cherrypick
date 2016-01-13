from cloudbench.benchmarks.cassandra_stress_test import cassandra_test

import re
import time

TIMEOUT=21600

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, cassandra_test)
    env.benchmark.executor.run()
