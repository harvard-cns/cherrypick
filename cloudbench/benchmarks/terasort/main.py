from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

from cloudbench.apps.pmbw import PMBW_PATH, PMBW_FILE, PMBW_REMOTE_PATH

import re

TIMEOUT=3600


def pmbw_test(vms, env):
    vm = vms[0]
    vm.install('hadoop')
    print "Done"

def run(env):
    vm1 = env.vm('vm-terasort')

    env.benchmark.executor([vm1], pmbw_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

