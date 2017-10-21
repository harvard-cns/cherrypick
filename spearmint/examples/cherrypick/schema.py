import os
from sqlobject import *

from aws import AWS_MACHINES

def create_database():
    map(lambda tbl: tbl.createTable(),
            [VirtualMachineType, DiskType, Machine,
             Configuration, Experiment, Run])
    create_virtual_machines()

def setup_connection():
    db_filename = os.path.abspath(os.path.join(__file__, '..', 'data', 'experiments.db'))
    connection_string = 'sqlite:' + db_filename
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection
    if not os.path.exists(db_filename):
        create_database()

def machine_cost(name):
    return AWS_MACHINES[name][0]

def machine_ram(name):
    return AWS_MACHINES[name][1]

def machine_cpu_count(name):
    return AWS_MACHINES[name][2]

def machine_cpu_speed(name):
    return {'r3': 'slow', 'm4': 'slow',
            'i2': 'slow', 'c4': 'fast'}[name[:2]]

def disk_speed(disk_type):
    return {'ebs': 'slow', 'local': 'fast'}[disk_type]

def disk_cost(name):
    if name == 'ebs':
        return 0.12
    return 0

def create_virtual_machines():
    for name in AWS_MACHINES:
        VirtualMachineType(name=name,
                ram=machine_ram(name),
                cpu_count=machine_cpu_count(name),
                speed=machine_cpu_speed(name),
                cost=machine_cost(name))

class VirtualMachineType(SQLObject):
    name = StringCol()
    ram = FloatCol()
    cpu_count = IntCol()
    speed = StringCol()
    cost = FloatCol()
    machines = MultipleJoin('Machine')

class DiskType(SQLObject):
    name = StringCol()
    disk_count = IntCol()
    speed = StringCol()
    cost = FloatCol()
    size = FloatCol()
    machines = MultipleJoin('Machine')

    @property
    def disk_cost(self):
        return self.cost * self.size

class Machine(SQLObject):
    disk = ForeignKey('DiskType')
    vm = ForeignKey('VirtualMachineType')
    configs = MultipleJoin('Configuration')

    @property
    def cost(self):
        return (self.vm.cost + self.disk.disk_cost / (30*24.0))/(3600.0)

class Configuration(SQLObject):
    count = IntCol()
    machine = ForeignKey('Machine')
    runs = MultipleJoin('Run')

    @property
    def cost(self):
        return self.machine.cost * self.count

    @property
    def cores(self):
        return self.machine.vm.cpu_count * self.count

    @property
    def vm_size(self):
        return self.machine.vm.name.split(".")[1]

    @property
    def vm_type(self):
        return self.machine.vm.name.split(".")[0]

    @property
    def ram(self):
        return self.machine.vm.ram * self.count

    @property
    def name(self):
        return "%d x %s.%s" % (self.count, self.vm_type, self.vm_size)

class Experiment(SQLObject):
    name = StringCol()
    runs = MultipleJoin('Run', joinColumn='exp_id')

    def find_runs(self, vm_name, count):
        vm = VirtualMachineType.selectBy(name=vm_name).getOne()
        machine = Machine.selectBy(vm=vm).getOne()
        config = Configuration.selectBy(machine=machine, count=count).getOne()
        return list(Run.selectBy(exp=self, config=config))

    @classmethod
    def find(kls, name):
        return kls.selectBy(name=name).getOne()

class Run(SQLObject):
    exp = ForeignKey('Experiment')
    config = ForeignKey('Configuration')
    time = FloatCol()
    num = IntCol()

    @property
    def cost(self):
        return self.config.cost * self.time

setup_connection()
