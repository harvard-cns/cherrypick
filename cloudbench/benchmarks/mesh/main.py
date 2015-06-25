from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from multiprocessing.pool import ThreadPool

from cloudbench.benchmarks.iperf.main import iperf
from cloudbench.benchmarks.hping.main import hping

import re
import traceback, sys

# Timeout of 50 minutes
TIMEOUT=50*60

def unixify(name):
    return name.lower().replace(' ', '_')

def save(env, results, benchmark, server, client):
    env.storage().save(results, partition=benchmark, key=(unixify(server) + '_' + unixify(client)))

# Iperf both sides
def experiment(params):
    vm1, vm2, env = params[0], params[1], params[2]
    try:
        # Save iperf results
        output = iperf(vm1, vm2, env)
        save(env, output, 'iperfmesh', vm1.location().location, vm2.location().location)

        # Save hping results
        output = hping(vm1, vm2, env)
        save(env, output, 'hpingmesh', vm2.location().location, vm1.location().location)
    except:
        print "Exception in user code:"
        print '-' * 60
        traceback.print_exc(file=sys.stdout)
        print '-' * 60
        exit()

def run(env):
    regions = {}

    # Categorize VMs based on their location
    for _, vm in env.virtual_machines().iteritems():
        group_name = vm.location().name
        if group_name not in regions:
            regions[group_name] = []
        regions[group_name].append(vm)


    def install(vm):
        vm.ssh() << WaitUntilFinished("sudo apt-get install hping3 -y")
        vm.ssh() << WaitUntilFinished("sudo apt-get install iperf -y")

    pool = ThreadPool(len(env.virtual_machines().values()))
    pool.map(install, env.virtual_machines().values())

    # Inter-location iperf/hping
    for key1 in regions:
        jobs = []
        for key2 in regions:
            if (key1 != key2):
                jobs.append((regions[key2][0], regions[key1][0], env,))
                
        pool = ThreadPool(len(env.locations())-1)
        pool.map(experiment, jobs)


    # Intra-location iperf/hping
    jobs = []
    for key1 in regions:
        jobs.append((regions[key1][0], regions[key1][1], env,))

    pool = ThreadPool(len(env.locations()))
    pool.map(experiment, jobs)
