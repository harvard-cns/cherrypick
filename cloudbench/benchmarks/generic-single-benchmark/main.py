from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from multiprocessing.pool import ThreadPool

from cloudbench.benchmarks.io.main import fio
from cloudbench.benchmarks.pmbw.main import pmbw
from cloudbench.benchmarks.hdparm.main import hdparm
from cloudbench.benchmarks.coremark.main import coremark, coremark_mp
from cloudbench.storage import JsonStorage

import json
import re
import traceback, sys

from threading import RLock

# Timeout of 50 minutes
TIMEOUT=50*60

def run_benchmarks(vms, env):
    vm1 = vms[0]

    #install(vm1)

    for iteration in range(1, 6):

        iobw = {}
        membw = {}
        coresp = {}
        coremp = {}
        hdres = {}

        while 'coremark_mp' not in coremp:
            vm1.script('sudo aptitude update')
            vm1.install('coremark')
            coremp = coremark_mp(vm1, env)

        while 'coremark' not in coresp:
            coresp = coremark(vm1, env)

        # while 'ScanWrite64PtrUnrollLoop' not in membw:
        #     vm1.script('sudo aptitude update')
        #     vm1.install('pmbw')
        #     membw  = pmbw(vm1, env)

        # while 'r70' not in iobw:
        #     vm1.script('sudo aptitude update')
        #     vm1.install('fio')
        #     iobw   = fio(vm1, env)

        iobw= { "w30" : "1",
                "server_location" : "us-west-1",
                "r100" : "1",
                "r70" : "1" }

        while 'hdparm_read' not in hdres:
            vm1.script('sudo aptitude update')
            vm1.install('hdparm')
            hdres = hdparm(vm1, env)

        res = {
           'coremp': coremp,
           'coresp': coresp,
           #'membw': membw,
           'iobw': iobw,
           'hdparm': hdres
        }

        storage = JsonStorage(env, vm1.type + '-' + str(iteration) + '-' + 'local' + '-hdparm' + '.json')
        #storage = JsonStorage(env, vm1.type + '-' + vm1.storage_type + '-hdparm' + '.json')
        storage.save(res)
        print ('Result: %s' % res)

def run(env):
    """ Run the mesh benchmark.
    
    Three different categories of experiments

    1) Intra data-center pairwise expeirments
    2) Inter data-center pairwise experiments
    3) Single VM experiments

    """

    env.benchmark.executor([env.vm('vm1')], run_benchmarks, '')
    env.benchmark.executor.run()
