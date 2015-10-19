CASSANDRA_URL='http://www.apache.org/dyn/closer.lua/cassandra/2.2.2/apache-cassandra-2.2.2-bin.tar.gz'
CASSANDRA_NAME='apache-cassandra-2.2.2-bin'
CASSANDRA_PATH='/usr/local/cassandra'

def install(vm):
    vm.install('java8')
    vm.script('rm -rf %s' % CASSANDRA_PATH)
    vm.script('wget -rc -nd %s' % CASSANDRA_URL)
    vm.script('tar -xzf %s.tar.gz' % CASSANDRA_NAME)
    vm.script('mv %s %s' % (CASSANDRA_NAME, CASSANDRA_PATH))

def remove(vm):
    vm.package_manager.installed('cassandra')
