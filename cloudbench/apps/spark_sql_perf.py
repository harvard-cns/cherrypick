from cloudbench.util import Config

SPARK_SQL_PERF_PATH='~/'
SPARK_SQL_PERF_DIR='%s/spark-sql-perf' % SPARK_SQL_PERF_PATH 
SPARK_SQL_PERF_FILE='spark-sql-perf.tar.gz'

def install(vm):
    vm.script("rm -rf %s" % SPARK_SQL_PERF_DIR);
    vm.send(Config.path('tools', SPARK_SQL_PERF_FILE), SPARK_SQL_PERF_PATH)
    vm.cd(SPARK_SQL_PERF_PATH).execute('tar xzf {0}'.format(SPARK_SQL_PERF_FILE));

def remove(vm):
    vm.rmdir(SPARK_SQL_PERF_DIR)

def installed(vm):
    return vm.isdir(SPARK_SQL_PERF_DIR)

