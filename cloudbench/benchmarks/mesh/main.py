from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug
from multiprocessing.pool import ThreadPool

from cloudbench.benchmarks.iperf.main import iperf, iperf_vnet
from cloudbench.benchmarks.hping.main import hping, hping_vnet
from cloudbench.benchmarks.io.main import fio

import re
import traceback, sys

from threading import RLock

# Timeout of 50 minutes
TIMEOUT=70*60

def unixify(name):
    return name.lower().replace(' ', '_')

def save(env, results, benchmark, server, client):
    env.storage().save(results, partition=benchmark, key=(unixify(server) + '_' + unixify(client)))

def install(vm):
    """ Install the required applications for the VM """

    if not hasattr(vm, '_install'):
        vm._install = True
        vm.ssh() << WaitUntilFinished("sudo apt-get install hping3 -y")
        vm.ssh() << WaitUntilFinished("sudo apt-get install iperf -y")
        vm.ssh() << WaitUntilFinished("sudo apt-get install fio -y")

        vm.install('coremark')
        vm.install('pmbw')

def inter_experiment(params):
    """ Run inter dc experiments """
    vm1, vm2, experiments, env = params
    try:

        # Save iperf results
        for exp in experiments:
            function = globals()[exp]
            def save_scope(func, exp):
                def execute(vms, env):
                    for vm in vms:
                        install(vm)
                    vm1, vm2 = vms
                    output = func(vm1, vm2, env)
                    save(env, output, exp+'mesh', vm1.location().location, vm2.location().location)
                return execute
            env.benchmark.executor([vm1, vm2], save_scope(function, exp), exp)
    except:
        print "Exception in user code:"
        print '-' * 60
        traceback.print_exc(file=sys.stdout)
        print '-' * 60
        exit()

def intra_experiment(params):
    """ Run intra dc experiments """
    vm1, vm2, experiments, env = params

    try:
        for exp in experiments:
            function = globals()[exp]
            def save_scope(func, exp):
                def execute(vms, env):
                    for vm in vms:
                        install(vm)
                    vm1, vm2 = vms
                    output = func(vm1, vm2, env)
                    save(env, output, exp+'mesh', vm1.location().location, vm2.location().location)
                return execute
            env.benchmark.executor([vm1, vm2], save_scope(function, exp), exp)
    except:
        print "Exception in user code:"
        print '-' * 60
        traceback.print_exc(file=sys.stdout)
        print '-' * 60
        exit()

def single_experiment(params):
    """ Runs single VM experiments """
    vm, experiments, env = params
    try:
        for exp in experiments:
            function = globals()[exp]

            def save_scope(func, exp):
                def execute(vms, env):
                    for vm in vms:
                        install(vm)
                    vm1 = vms[0]
                    output = func(vm1, env)
                    save(env, output, exp+'mesh', vm1.location().location, vm1.location().location)
                return execute
            env.benchmark.executor([vm], save_scope(function, exp), exp)
    except:
        print "Exception in user code:"
        print '-' * 60
        traceback.print_exc(file=sys.stdout)
        print '-' * 60
        exit()

def categorize(env):
    """ Categorize the available virtual machines in each region"""
    regions = {}
    # Categorize VMs based on their location
    for _, vm in env.virtual_machines().iteritems():
        group_name = vm.location().name
        if group_name not in regions:
            regions[group_name] = []
        regions[group_name].append(vm)

    return regions

def single_dc(regions, env, experiments):
    """ Run the intra-dc experiments """
    jobs = []
    for key1 in regions:
        jobs.append((regions[key1][1], experiments, env,))

    for job in jobs:
        single_experiment(job)

def intra_dc(regions, env, experiments):
    """ Run the intra-dc experiments """
    jobs = []
    for key1 in regions:
        jobs.append((regions[key1][0], regions[key1][1], experiments, env,))

    for job in jobs:
        intra_experiment(job)

def inter_dc(regions, env, experiments):
    """ Run inter-dc experiments between all pairs of VMs
        
    The order of execution is such that no virtual machine will be
    executing two benchmarks at the same time.
    """
    region_names = regions.keys()
    start = 1

    # Inter-location iperf/hping
    for start in range(1, len(env.locations())):
        jobs = []
        for idx, reg_src in enumerate(region_names):
            reg_dst = region_names[(start + idx) % len(region_names)]
            jobs.append((regions[reg_src][0], regions[reg_dst][1],
                experiments, env,))

        for job in jobs:
            inter_experiment(job)


def run(env):
    """ Run the mesh benchmark.
    
    Three different categories of experiments

    1) Intra data-center pairwise expeirments
    2) Inter data-center pairwise experiments
    3) Single VM experiments

    """
    regions = {}

    inter_dc_experiments = ['iperf', 'hping']
    intra_dc_experiments = ['iperf_vnet', 'hping', 'iperf']
    single_dc_experiments = ['coremark', 'fio', 'pmbw']

    regions = categorize(env)

    #prepare(env)
    single_dc(regions, env, single_dc_experiments)
    intra_dc(regions, env, intra_dc_experiments)
    inter_dc(regions, env, inter_dc_experiments)

    env.benchmark.executor.run()
    #env.benchmark.executor.stop()
