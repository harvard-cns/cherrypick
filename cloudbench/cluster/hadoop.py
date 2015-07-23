from .base import Cluster

# The instruction is taken from:

class HadoopCluster(Cluster):
    def __init__(self, *args, **kwargs):
        super(HadoopCluster, self).__init__(*args, **kwargs)

    def configure(self):
        pass

    def name_node(self, vm):
        pass

    def resource_manager(self, vm):
        pass

    def data_node(self, vm):
        pass
