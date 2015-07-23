from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.pmbw import PMBW_PATH, PMBW_FILE, PMBW_REMOTE_PATH
from cloudbench.cluster.base import Cluster

import re

TIMEOUT=3600


def terasort_test(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)

    cluster = Cluster(vms, 'hduser')
    cluster.setup_keys()
    #cluster.configure()

def run(env):
    vm1 = env.vm('vm1')
    vm2 = env.vm('vm2')

    env.benchmark.executor([vm1, vm2], terasort_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

