import os

from .base import Cluster
from cloudbench.apps.cassandra import CASSANDRA_USER, CASSANDRA_DIR
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
rpc_address: 0.0.0.0
endpoint_snitch: %s
"""

class CassandraCluster(Cluster):
    def __init__(self, vms, datapath='/cassandra-data', name='MyCassandraCluster', snitch='RackInferringSnitch'):
        self._snitch = snitch
        self._nodes = vms
        self._seed = vms[0]
        self._name = name
        self._datapath = datapath

    @property
    def name(self):
        return self._name

    @property
    def seeds(self):
        return [self._seed]

    @property
    def nodes(self):
        return self._nodes

    @property
    def snitch(self):
        return self._snitch

    @property
    def datapath(self):
        return self._datapath

    def reset(self):
        data_folder = '%s/data' % self.datapath
        log_folder = '%s/commitlog' % self.datapath
        vm.script('rm -rf %s' % data_folder)
        vm.script('rm -rf %s' % log_folder)
        vm.script('mkdir %s' % data_folder)
        vm.script('mkdir %s' % log_folder)
        vm.script('chown -R ubuntu:ubuntu %s' % data_folder)
        vm.script('chown -R ubuntu:ubuntu %s' % log_folder)

    def kill_single_instance(self, vm):
        vm.script('pkill cassandra')

    def kill(self):
        parallel(self.kill_single_instance, self.nodes)

    def start_single_instance(self, vm):
        vm.script('sudo su - ubuntu - && cd %s && ./bin/cassandra')

    def setup(self):
        template = []
        cur_dir = os.path.dirname(__file__)
        yaml = os.path.join(cur_dir, 'cassandra.yaml')

        basedata = ''
        with open(yaml, 'r') as f:
            basedata = f.read()

        conndata = CassandraTemplate % (
                    self.datapath, self.datapath,
                    ','.join(self.seeds))

        def write_yaml(vm):
            pernodedata = CassandraBase % (
                    self.name, 
                    vm.intf_ip('eth0'),
                    self.snitch)

            config = "\n".join([basedata, pernodedata, conndata])
            vm.script('sudo cat <<EOT > {0}/conf/cassandra.yaml\n{1}\nEOT'.format(CASSANDRA_PATH, config))
        parallel(write_yaml, self.nodes)
