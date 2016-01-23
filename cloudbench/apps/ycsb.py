YCSB_PATH="~/YCSB"

def install(vm):
    vm.install('git')
    vm.install('maven')
    vm.script('git clone https://github.com/brianfrankcooper/YCSB %s' % YCSB_PATH)
    vm.script('cd %s && git checkout tags/0.5.0 -b stable' % YCSB_PATH)
