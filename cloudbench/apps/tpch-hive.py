from cloudbench.util import Config

TPCH_HIVE_PATH='~/'
TPCH_HIVE_FILE='hive-tpch.tar.gz'

def install(vm):
    vm.script("rm -rf ~/hive-tpch");
    vm.send(Config.path('tools', TPCH_HIVE_FILE), TPCH_HIVE_PATH)
    vm.cd(TPCH_HIVE_PATH).execute('tar xzf {0}'.format(TPCH_HIVE_FILE));

def remove(vm):
    vm.rmdir(TPCH_HIVE_PATH + '/hive-tpch')

def installed(vm):
    return vm.isdir(TPCH_HIVE_PATH + '/hive-tpch')

