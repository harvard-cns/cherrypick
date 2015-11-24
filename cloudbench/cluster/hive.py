from .hadoop import HadoopCluster
from cloudbench.apps.hadoop import HADOOP_USER, HADOOP_DIR

class HiveCluster(object):
    def __init__(self, hadoop_cluster):
        self.hc_ = hadoop_cluster

    @property
    def cluster(self):
        return self.hc_

    def setup(self):
        def setup_hive(vm):
            vm.script('sudo su {0} -c hadoop fs -mkdir /usr/hive/warehouse'.format(HADOOP_USER))
            vm.script('sudo su {0} -c hadoop fs -chmod g+w /usr/hive/warehouse'.format(HADOOP_USER))
        setup_hive(self.cluster.master)

    @property
    def master(self):
        return self.hc_.master
