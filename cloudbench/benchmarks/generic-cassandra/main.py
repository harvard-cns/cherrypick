from cloudbench.util import Debug, parallel

from cloudbench.apps.cassandra import CASSANDRA_PATH
from cloudbench.cluster.cassandra import CassandraCluster

import re
import time

TIMEOUT=21600

def cassandra_test(vms, env):
    parallel(lambda x: x.install('cassandra'), vms)

    CassandraData = '/cassandra-data'
    def setup_disk(vm):
        vm.mount('/dev/xvdb', CassandraData, force_format='True')

    parallel(setup_disk, vms)
    cluster = CassandraCluster(vms, CassandraData)
    cluster.kill()
    cluster.reset()
    cluster.setup()


def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, cassandra_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

