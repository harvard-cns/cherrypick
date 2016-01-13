import os
import Queue
import time

from .base import Cluster
from cloudbench.apps.cassandra import CASSANDRA_USER, CASSANDRA_GROUP, CASSANDRA_PATH
from cloudbench.util import parallel

CassandraTemplate="""
seed_provider:
    - class_name: org.apache.cassandra.locator.SimpleSeedProvider
      parameters:
          - seeds:  "%s"

data_file_directories:
    - %s/data

commitlog_directory: %s/commitlog
"""
CassandraBase="""
cluster_name: '%s'
num_tokens: 256
listen_address: %s
rpc_address: %s
endpoint_snitch: %s
"""

class CassandraCluster(Cluster):
    def __init__(self, vms, test_vms, name='MyCassandraCluster', snitch='RackInferringSnitch'):
        self._snitch = snitch
        self._nodes = vms
        self._seed = vms[0]
        self._test_vms = test_vms
        self._name = name
        #self._datapath = 

    @property
    def name(self):
        return self._name

    @property
    def seeds(self):
        return [self._seed]

    @property
    def seed_ips(self):
        return map(lambda x: x.intf_ip('eth0'), self.seeds)

    @property
    def nodes(self):
        return self._nodes

    @property
    def snitch(self):
        return self._snitch

    @property
    def datapath(self):
        return self._datapath

    def reset_single_instance(self, vm):
        vm_parts = vm.data_directories()
        parallel(lambda d: vm.script("rm -rf %s/{data,commitlog}" % d), vm_parts)

    def reset(self):
        parallel(self.reset_single_instance, self.nodes)

    def kill_single_instance(self, vm):
        vm.script('pkill -9 java')

    def kill(self):
        parallel(self.kill_single_instance, self.nodes)

    def start_single_instance(self, vm):
        vm.script('sudo su - %s -c "cd %s && ./bin/cassandra"' % (CASSANDRA_USER, CASSANDRA_PATH))

    def start(self):
        parallel(self.start_single_instance, self.seeds)
        for vm in [x for x in self.nodes if x not in self.seeds]:
            self.start_single_instance(vm)

    def setup(self):
        template = []
        cur_dir = os.path.dirname(__file__)
        yaml = os.path.join(cur_dir, 'cassandra.yaml')

        basedata = ''
        with open(yaml, 'r') as f:
            basedata = f.read()


        def write_yaml(vm):
            pernodedata = CassandraBase % (
                    self.name, 
                    vm.intf_ip('eth0'),
                    vm.intf_ip('eth0'),
                    self.snitch)

            vm_parts = vm.data_directories()

            data_dirs = ("/data\n    - ").join(vm_parts)
            commit_dirs = vm_parts[0]
            if len(vm_parts) > 1:
                data_dirs = ("/data\n    - ").join(vm_parts[1:])

            conndata = CassandraTemplate % (
                        ','.join(self.seed_ips),
                        data_dirs, commit_dirs)

            config = "\n".join([basedata, pernodedata, conndata])
            vm.script('sudo cat <<EOT > {0}/conf/cassandra.yaml\n{1}\nEOT'.format(CASSANDRA_PATH, config))
        parallel(write_yaml, self.nodes)

    def node_ip_list(self):
        return map(lambda node: node.intf_ip('eth0'), self.nodes)


    def run_on_testers(self, func):
        result = Queue.Queue()
        parallel(lambda vm: result.put(func(vm)), self._test_vms)

        out = []
        while not result.empty():
            out.append(result.get())
        return out

    def stress_test_write(self, size):
        return self.run_on_testers(lambda vm:
            vm.script("cd %s; ./tools/bin/cassandra-stress write n=%s -node %s | tail -n 100" % (
                CASSANDRA_PATH, str(size), ','.join(self.node_ip_list()))))

    def stress_test_read(self):
        return self.run_on_testers(lambda vm:
            vm.script("cd %s; ./tools/bin/cassandra-stress read -node %s | tail -n 100" % (
                CASSANDRA_PATH, ','.join(self.node_ip_list()))))

    def stress_test_mixed(self, write, read):
        return self.run_on_testers(lambda vm:
            vm.script("cd %s; ./tools/bin/cassandra-stress mixed ratio\\(write=%s,read=%s\\) -node %s -rate threads\\>=100 | tail -n 100" % (
                CASSANDRA_PATH, str(write), str(read), ','.join(self.node_ip_list()))))

    def stress_test_mixed_with_thread_count(self, write, read, count, thread_count):
        return self.run_on_testers(lambda vm:
            vm.script("cd %s; ./tools/bin/cassandra-stress mixed ratio\\(write=%s,read=%s\\) n=%d -node %s -rate threads\\>=%d threads\\<=%d | tail -n 100" % (
            CASSANDRA_PATH, str(write), str(read), count, ','.join(self.node_ip_list()), thread_count, thread_count)))

