#CASSANDRA_URL='http://www.apache.org/dyn/closer.lua/cassandra/2.2.2/apache-cassandra-2.2.2-bin.tar.gz'
#CASSANDRA_URL='http://www.apache.org/dyn/closer.lua/cassandra/2.2.2/apache-cassandra-2.2.2-bin.tar.gz'
CASSANDRA_URL='http://apache.arvixe.com/cassandra/2.2.4/apache-cassandra-2.2.4-bin.tar.gz'
CASSANDRA_NAME='apache-cassandra-2.2.4'
CASSANDRA_PATH='/usr/local/cassandra'
CASSANDRA_USER='ubuntu'
CASSANDRA_GROUP='ubuntu'

def install(vm):
    vm.install('java8')
    vm.script('pkill -9 java')
    vm.script('rm -rf %s' % CASSANDRA_PATH)
    vm.script('wget -rc -nd %s' % CASSANDRA_URL)
    vm.script('tar -xzf %s-bin.tar.gz' % CASSANDRA_NAME)
    vm.script('mv %s %s' % (CASSANDRA_NAME, CASSANDRA_PATH))
    vm.script('chown -R %s:%s %s' % (CASSANDRA_USER, CASSANDRA_GROUP, CASSANDRA_PATH))

def remove(vm):
    vm.package_manager.installed('cassandra')
