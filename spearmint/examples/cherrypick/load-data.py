from schema import *

import glob
import os

def _find_or_create_class(kls, *args, **kwargs):
    objs = list(kls.selectBy(*args, **kwargs))
    if objs:
        return objs[0]
    return kls(*args, **kwargs)

def find_or_create_machine(name, disk_type, disk_count):
    vm = VirtualMachineType.selectBy(name=name).getOne()
    dts = list(DiskType.selectBy(name=disk_type, disk_count=disk_count))
    if not dts:
        dts = [DiskType(name=disk_type, disk_count=disk_count,
                        cost=disk_cost(disk_type), size=500,
                        speed=disk_speed(disk_type))]
    return _find_or_create_class(Machine, disk=dts[0], vm=vm)

def find_or_create_configuration(machine, count):
    return _find_or_create_class(Configuration, machine=machine, count=count)

def find_or_create_experiment(name):
    return _find_or_create_class(Experiment, name=name)

def find_or_create_run(exp, num, vm, count, dtype, dcount, time):
    num = int(num)
    count = int(count)
    dcount = int(dcount)
    time = float(time)

    exp = find_or_create_experiment(exp)
    machine = find_or_create_machine(vm, dtype, dcount)
    configuration = find_or_create_configuration(machine, count)
    runs = list(Run.selectBy(config=configuration, exp=exp, num=num))

    if runs:
        return
    Run(exp=exp, config=configuration, time=time, num=num)


def load_file(fname):
    with open(fname, 'r') as f:
        for line in f:
            args = line.strip().split("\t")
            print args
            find_or_create_run(*args)

def load_result_directories(directory):
    wildcard_path = os.path.join(os.path.abspath(directory), "*.tsv")
    for fname in glob.glob(wildcard_path):
        load_file(fname)

if __name__ == '__main__':
    load_result_directories(directory="results")
