import math

from cherrypick_config import *
from schema import *

def vm_name(cpu_type, cpu_count, ram, disk_type):
    cpu_type = cpu_type[0]
    cpu_count = cpu_count[0]
    ram = ram[0]
    disk_type = disk_type[0]

    prefix = None
    print cpu_type, ram, disk_type, cpu_count
    if cpu_type == 'slow' and ram == 'medium' and disk_type == 'slow':
        prefix = 'm4'
    if cpu_type == 'slow' and ram == 'high' and disk_type == 'slow':
        prefix = 'r3'
    if cpu_type == 'fast' and ram == 'low' and disk_type == 'slow':
        prefix = 'c4'
    if cpu_type == 'slow' and ram == 'high' and disk_type == 'fast':
        prefix = 'i2'
    if prefix is None:
        raise Exception("Invalid VM type.")

    suffix=None
    if cpu_count == 2:
        suffix = 'large'
    elif cpu_count == 4:
        suffix = 'xlarge'
    elif cpu_count == 8:
        suffix = '2xlarge'
    if suffix is None:
        raise Exception("Invalid VM size.")
    return ".".join([prefix, suffix])

def cluster_size_normalized(name, size):
    vm_size = {'large': 4, 'xlarge': 2, '2xlarge': 1}[name.split(".")[1]]
    return vm_size * 2 * size

def find_runs(spec):
    cpu_type = spec['cpu_type']
    cpu_count = spec['cpu_count']
    cluster_size = spec['machine_count']
    disk_type = spec['disk_type']
    ram = spec['ram']
    vm = vm_name(cpu_type, cpu_count, ram, disk_type)
    exp = Experiment.find(EXPERIMENT)
    runs = exp.find_runs(vm, cluster_size_normalized(vm, int(cluster_size)))
    print "[@]> %s\t%s\t%d\t%.2f\t%.4f\t%.4f" % (exp.name, vm, int(cluster_size), runs[0].time, runs[0].cost, COST_FUNC(runs[0]))
    return runs[0]

def main(job_id, params):
    return COST_FUNC(find_runs(params))
