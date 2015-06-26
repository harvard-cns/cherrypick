from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from multiprocessing.pool import ThreadPool

from cloudbench.benchmarks.iperf.main import iperf, iperf_vnet
from cloudbench.benchmarks.hping.main import hping, hping_vnet

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
    vm1, vm2, env = params
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

def vnet_experiment(params):
    vm1, vm2, env = params

    try:
        # output = hping_vnet(vm1, vm2, env)
        # save(env, output, 'hpingmeshvnet', vm2.location().location, vm1.location().location)

        output = iperf_vnet(vm1, vm2, env)
        save(env, output, 'iperfmeshvnet', vm1.location().location, vm2.location().location)
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

    region_names = regions.keys()
    start = 1

    # VNet iperf/hping
    jobs = []
    for key1 in regions:
        jobs.append((regions[key1][0], regions[key1][1], env,))

    pool = ThreadPool(len(env.locations()))
    pool.map(vnet_experiment, jobs)

    # Inter-location iperf/hping
    for start in range(1, len(env.locations())):
        jobs = []
        for idx, reg_src in enumerate(region_names):
            reg_dst = region_names[(start + idx) % len(region_names)]
            jobs.append((regions[reg_src][0], regions[reg_dst][1], env,))
        pool = ThreadPool(len(env.locations())-1)
        pool.map(experiment, jobs)


    # Intra-location iperf/hping
    jobs = []
    for key1 in regions:
        jobs.append((regions[key1][0], regions[key1][1], env,))

    pool = ThreadPool(len(env.locations()))
    pool.map(experiment, jobs)

