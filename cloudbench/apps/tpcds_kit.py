from cloudbench.util import Config

TPCDS_PATH='~/'
TPCDS_DIR='%s/tpcds-kit' % TPCDS_PATH 

def install(vm):
    vm.install('git')
    vm.install('build-essential')
    vm.package_manager.install('flex')
    vm.package_manager.install('bison')
    vm.script('git clone https://github.com/SiGe/tpcds-kit.git')
    vm.script('cd tpcds-kit/tools; make -f Makefile.suite')

def remove(vm):
    vm.rmdir(TPCDS_DIR)

def installed(vm):
    return vm.isdir(TPCDS_DIR)

