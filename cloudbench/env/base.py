from cloudbench.env.config.xml_config import EnvXmlConfig
from cloudbench.env.clouds import AzureCloud, AwsCloud
from cloudbench.storage import AzureStorage, FileStorage, JsonStorage
from cloudbench.util import parallel

import threading
import time
import os

class Benchmark(object):
    """Wraps the benchmark parameters"""
    def __init__(self, name, directory, env):
        """Initialize the benchmark object

        name -- name of the benchmark that will get executed
        directory -- directory to look for the benchmark and also save the results.
        env -- environment of the execution, e.g., the virtual machines, etc.
        """
        self._config = None
        self._env = env
        self._name = name

        self._file = os.path.join(directory, 'config.xml')

        self._storage_path = os.path.join(directory, env.cloud_name + '.json')
        self._storage = None

    @property
    def name(self):
        return self._name

    @property
    def env(self):
        return self._env

    @property
    def config(self):
        """ Return the configuration """
        if self._config:
            return self._config
        if '.xml' in self._file:
            self._config = EnvXmlConfig(self._file, self.env.cloud_name, self.env)
            self._config.parse()

        return self._config

    @property
    def data(self):
        if self._storage:
            return self._storage

        self._storage = JsonStorage(self._env, self._storage_path)
        return self._storage

class Env(object):
    def __init__(self, cloud, f, benchmark, storage):
        self._cloud = cloud
        self._file = f
        self._config = None
        self._manager = None
        self._storage = storage
        self._uuid = 'cb'
        self._test = False

        self._benchmark = Benchmark(benchmark, 
                os.path.abspath(os.path.join(self._file, os.pardir)),
                self)

    def test(self, val):
        self._test = not (not val)

    def is_test(self):
        return self._test

    @property
    def config(self):
        """ Return the configuration """
        return self.benchmark.config

    @property
    def manager(self):
        """ Return the manager """
        if self._manager:
            return self._manager

        if self._cloud == 'azure':
            self._manager = AzureCloud(self)
        elif self._cloud == 'aws':
            self._manager = AwsCloud(self)

        return self._manager

    def storage(self):
        """ Return the storage where we save the resulting data """
        if isinstance(self._storage, str):
            if self._storage == 'azure':
                self._storage = AzureStorage(self)

        return self._storage

    @property
    def benchmark(self):
        """ Returns the active benchmark """
        return self._benchmark

    @property
    def cloud_name(self):
        """ Returns the name of the cloud provider """
        return self._cloud

    def vm(self, name):
        """ Shorthand to find a virtual-machine """
        return self.virtual_machines()[name]

    # Delegate these calls to the manager, maybe he knows what to do
    # with them?
    def __getattr__(self, name):
        """ Delegates methods that are not defined to the manager """

        if name.startswith('create') or name.startswith('delete'):
            if hasattr(self.manager, name):
                return getattr(self.manager, name)

            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, name))

        return getattr(self.config, name)

    def traverse_dag(self, check, execute, direction='dependencies'):
        """ Traverse from the leaves upward to root, making sure all
        the leaves of a node have executed the "execute" function before
        the node is executed """

        def satisfied(ent):
            """ Returns true if the requirement of an entity are
            satisfied """
            for dep in getattr(ent, direction):
                deps = getattr(ent, dep)()
                if not deps:
                    continue

                if not isinstance(deps, list):
                    deps = [deps]

                # if any of the dependencies are not satisfied, return False
                if any(map(lambda x: not check(x), deps)):
                    return False

            return True

        # Collect all entities
        everything = set()
        for ent in self.entities().values():
            everything = everything.union(set(ent.values()))

        while everything:
            to_remove = set()
            to_execute = set()
            for ent in everything:
                if satisfied(ent):
                    if not check(ent):
                        to_execute.add(ent)
                    else:
                        to_remove.add(ent)

            parallel(lambda x: execute(x), to_execute)
            to_remove = to_remove.union(set(filter(lambda x: check(x), to_execute)))
            everything = everything - to_remove

    def setup(self):
        """ Setup the VMs """
        self.traverse_dag(lambda x: x.created(),
                          lambda x: x.create(),
                          'dependencies')

    def teardown(self):
        """ Delete everything """
        self.traverse_dag(lambda x: x.deleted(),
                          lambda x: x.delete(),
                          'dependents')

    def start(self):
        """ Start the topology in parallel """
        self.traverse_dag(lambda x: x.started(),
                          lambda x: x.start(),
                          'dependencies')

    def stop(self):
        """ Stop the topology in parallel """
        self.traverse_dag(lambda x: x.stopped(),
                          lambda x: x.stop(),
                          'dependents')
