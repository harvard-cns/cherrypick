import math
from .template import write_template 
from cloudbench.util import Debug, parallel

class ClouderaPackage(object):
    def __init__(self, cloudera):
        self.cloudera_ = cloudera

    def setup(self):
        pass

    @property
    def cloudera(self):
        return self.cloudera_

    @property
    def nodes(self):
        return self.cloudera_.nodes

class ClouderaHadoop(ClouderaPackage):
    def __init__(self, cloudera):
        self.master_ = cloudera.nodes[0]

        # Everyone is a worker
        self.workers_ = cloudera.nodes

        #if len(cloudera.nodes) > 6:
            # If we have more than ten cloudera nodes, dedicate the master to management
        self.workers_ = cloudera.nodes[1:]

        super(ClouderaHadoop, self).__init__(cloudera)

    @property
    def master(self):
        return self.master_

    @property
    def workers(self):
        return self.workers_

    MasterPackages = [
            'hadoop-yarn-resourcemanager',
            'hadoop-hdfs-namenode',
            'hadoop-mapreduce-historyserver',
            'hadoop-yarn-proxyserver']

    WorkerPackages = [
            'hadoop-yarn-nodemanager',
            'hadoop-hdfs-datanode', 
            'hadoop-mapreduce',
            'hadoop-client']

    def install_master(self):
        for package in ClouderaHadoop.MasterPackages:
            self.master.package_manager.install(package)

    def install_workers(self):
        def install_worker_packages(vm):
            for package in ClouderaHadoop.WorkerPackages:
                vm.package_manager.install(package)

        parallel(install_worker_packages, self.nodes)

    def setup_directories(self):
        def create_yarn_dfs_folders(vm):
            if len(vm.data_directories()) == 0:
                vm.script("mkdir -p /data/1/")

            for dd in vm.data_directories():
                vm.script("rm -r {base}/yarn".format(base=dd))
                vm.script("rm -r {base}/dfs".format(base=dd))

                vm.script("mkdir -p {base}/yarn/logs".format(base=dd))
                vm.script("mkdir -p {base}/yarn/local".format(base=dd))
                vm.script("chown -R yarn:yarn {base}/yarn".format(base=dd))

                vm.script("mkdir -p {base}/dfs/nn".format(base=dd))
                vm.script("mkdir -p {base}/dfs/dn".format(base=dd))
                vm.script("chown -R hdfs:hdfs {base}/dfs".format(base=dd))
        parallel(create_yarn_dfs_folders, self.nodes)

    def restart_hdfs(self):
        self.master.script('sudo service hadoop-hdfs-namenode restart')
        parallel(lambda vm: vm.script('sudo service hadoop-hdfs-datanode restart'), self.workers)

        self.master.script('sudo -u hdfs hdfs dfs -mkdir -p /tmp/hadoop-yarn')
        self.master.script('sudo -u hdfs hdfs dfs -chmod -R 1777 /tmp')
        self.master.script('sudo -u hdfs hdfs dfs -chmod -R 1777 /tmp/hadoop-yarn')

    def restart_yarn(self):
        #self.master.script('sudo service hadoop-yarn-nodemanager restart')
        self.master.script('sudo service hadoop-yarn-nodemanager stop')
        self.master.script('sudo service hadoop-yarn-resourcemanager restart')
        self.master.script('sudo service hadoop-mapreduce-historyserver restart')
        parallel(lambda vm: vm.script('sudo service hadoop-yarn-nodemanager restart'), self.workers)

    def available_memory(self, vm):
        #return int(vm.memory() / (1024 * 1024)) - 512
        ram_mb = int(vm.memory() / (1024*1024))
        if ram_mb > 100*1024:
            return ram_mb - 15 * 1024
        elif ram_mb > 60*1024:
            return ram_mb - 10 * 1024
        elif ram_mb > 40*1024:
            return ram_mb - 6 * 1024
        elif ram_mb > 20*1024:
            return ram_mb - 3 * 1024
        elif ram_mb > 10*1024:
            return ram_mb - 2 * 1024
        return max(512, ram_mb - 1300)

    def setup_configuration(self):
        def setup_yarn(vm, is_master):
            def setup_yarn_site():
                data_directories = vm.data_directories()
                total_cpu = vm.cpus()
                total_memory = self.available_memory(vm)
                ammem = min(1536, total_memory - 100)
                mapmem = total_memory/total_cpu
                reducemem = mapmem
                mapmemheap = int(0.8 * mapmem)
                reducememheap = int(0.8 * reducemem)

                localdirs = []
                for d in data_directories:
                    localdirs.append("file://%s/hadoop-yarn/cache/\${user.name}/nm-local-dir" % d)

                for d in data_directories:
                    vm.script("mkdir -p %s/hadoop-yarn/cache" % d)
                    vm.script("chmod -R 777 %s/hadoop-yarn" % d)

                vm.script(write_template('yarn-site',
                    '/etc/hadoop/conf.my_cluster/yarn-site.xml',
                    master=self.master.name,
                    totalmem=total_memory,
                    totalcpu=total_cpu,
                    # clustermem=total_memory*len(self.nodes),
                    # clustercpu=total_cpu*len(self.nodes),
                    localdirs=','.join(localdirs),
                    ammem=ammem,
                    mapmem=mapmem,
                    mapmemheap=mapmemheap,
                    reducemem=reducemem,
                    reducememheap=reducememheap))

            def setup_yarn_directories():
                self.master.script('sudo -u hdfs hdfs dfs -mkdir -p /var/log/hadoop-yarn/apps')
                self.master.script('sudo -u hdfs hdfs dfs -chown -R yarn:yarn /var/log/hadoop-yarn/apps')

            def setup_historyserver_directories():
                self.master.script('sudo -u hdfs hadoop fs -mkdir -p /user/history')
                self.master.script('sudo -u hdfs hadoop fs -chmod -R 1777 /user/history')
                self.master.script('sudo -u hdfs hadoop fs -chown mapred:hadoop /user/history')

            setup_yarn_directories()
            setup_yarn_site()
            setup_historyserver_directories()

        def setup_hdfs(vm):
            def delete_corpses():
                vm.script('rm -rf /tmp/hadoop-hdfs/')

            def duplicate_configuration():
                vm.script("cp -r /etc/hadoop/conf.empty /etc/hadoop/conf.my_cluster")
                vm.script("update-alternatives --install /etc/hadoop/conf hadoop-conf /etc/hadoop/conf.my_cluster 50")
                vm.script("update-alternatives --set hadoop-conf /etc/hadoop/conf.my_cluster")

            def setup_core_site():
                data_directories = vm.data_directories()
                tmpdir = data_directories[0] + '/hadoop-tmp'
                vm.script('mkdir -p %s' % tmpdir)
                vm.script('chmod 777 -R %s' % tmpdir)

                vm.script(write_template('core-site',
                    '/etc/hadoop/conf.my_cluster/core-site.xml',
                    master=self.master.name,
                    tmpdir=tmpdir))

            def setup_mapred_site():
                vm.script(write_template('mapred-site',
                    '/etc/hadoop/conf.my_cluster/mapred-site.xml',
                    framework='yarn'))

            def setup_hdfs_site():
                data_directories = vm.data_directories()
                datanodes = ['file://' + d + '/dfs/dn' for d in data_directories]
                namenodes = ['file://' + d + '/dfs/nn' for d in data_directories]

                vm.script(write_template('hdfs-site',
                    '/etc/hadoop/conf.my_cluster/hdfs-site.xml',
                    datanodes=','.join(datanodes),
                    namenodes=','.join(namenodes)))

            duplicate_configuration()

            delete_corpses()
            setup_core_site()
            setup_hdfs_site()
            setup_mapred_site()

        parallel(lambda vm: setup_hdfs(vm), self.nodes)
        self.master.script('sudo -u hdfs hdfs namenode -format')
        self.restart_hdfs()
        parallel(lambda vm: setup_yarn(vm, vm == self.master), self.nodes)
        self.restart_yarn()
        self.master.script('sudo -u hdfs hdfs dfs -chmod -R 1777 /tmp')
        self.master.script('sudo -u hdfs hdfs dfs -chmod -R 1777 /user')
        self.master.script('sudo -u hdfs hdfs dfs -chmod -R 1777 /tmp/hadoop-yarn')

    def setup(self):
        self.install_master()
        self.install_workers()
        self.setup_directories()
        self.setup_configuration()
        return True

    def execute(self, command):
        return self.master.script('{cmd}'.format(cmd=command))

class ClouderaSpark(ClouderaPackage):
    def __init__(self, cloudera):
        super(ClouderaSpark, self).__init__(cloudera)

    SparkPackages = [
            'spark-core', 
            'spark-history-server',
            'spark-python']

    def setup(self):
        hadoop = self.cloudera.install('Hadoop')
        if not hadoop:
            return False

        def install_spark(vm):
            for package_name in ClouderaSpark.SparkPackages:
                vm.package_manager.install(package_name)
        parallel(install_spark, self.nodes)

        hadoop.execute('sudo -u hdfs hdfs dfs -mkdir -p /user/spark')
        hadoop.execute('sudo -u hdfs hdfs dfs -mkdir -p /user/spark/share/lib')
        hadoop.execute('sudo -u hdfs hdfs dfs -mkdir -p /user/spark/applicationHistory')
        hadoop.execute('sudo -u hdfs hdfs dfs -chown -R spark:spark /user/spark')
        hadoop.execute('sudo -u hdfs hdfs dfs -chmod 1777 /user/spark/applicationHistory')

        per_node_cpu= self.master.cpus()
        cluster_cpu = per_node_cpu* len(self.nodes)
        total_memory = int(self.master.memory() / (1024 * 1024)) - 1024

        # executor_memory = int(total_memory/(per_node_cpu*1024))
        # executor_count = cluster_cpu
        # executor_cores = 1

        executor_count = cluster_cpu
        executor_cores = 1
        executor_memory = int(math.ceil(total_memory*executor_cores/per_node_cpu)*0.5)#int(math.ceil((total_memory - 5.0*1024/len(self.nodes) - 1024)*0.90))

        self.master.script(write_template('spark-defaults.conf',
            '/etc/spark/conf/spark-defaults.conf',
            master=self.master.name,
            instances=executor_count,
            cores=executor_cores,
            memory=(str(executor_memory) + 'm')))

        self.master.script('sudo service spark-history-server restart')
        return True

    @property
    def master(self):
        return self.cloudera['Hadoop'].master

    @property
    def workers(self):
        return self.cloudera['Hadoop'].workers

class ClouderaHive(ClouderaPackage):
    def __init__(self, cloudera):
        super(ClouderaHive, self).__init__(cloudera)

    HivePackages = [
            'hive',
            'hive-metastore'
            ]

    @property
    def master(self):
        return self.cloudera['Hadoop'].master
            
    def setup(self):
        if not self.cloudera.install('Hadoop'):
            return False

        if not self.cloudera.install('Spark'):
            return False

        def install_hive(vm):
            for package_name in ClouderaHive.HivePackages:
                vm.package_manager.install(package_name)
        parallel(install_hive, self.nodes)

        def setup_mysql():
            vm = self.master
            sqlFile = '/usr/lib/hive/setup-mysql-cloudbench.sql'
            vm.install('mysql')
            vm.script(write_template('hive-mysql', sqlFile))
            vm.script('cat {0} | mysql -u root'.format(sqlFile))

        def setup_hive(vm):
            vm.script(write_template('hive-site', '/usr/lib/hive/conf/hive-site.xml',
                master=self.master.name))

        # Install mysql on the master
        setup_mysql()
        parallel(setup_hive, self.nodes)

        return True


class Cloudera(object):
    def __init__(self, vms):
        self.vms_ = vms
        self.packages_ = {}
        self.is_setup_ = False

    def installed(self, package_name):
        return package_name in self.packages_

    def install(self, package_name):
        if not self.is_setup_:
            self.setup()

        if not self.installed(package_name):
            app = globals()['Cloudera' + package_name](self)
            if app.setup():
                self.packages_[package_name] = app
                return app

            return None
        else:
            return self.packages_[package_name]

    def __getitem__(self, name):
        if name in self.packages_:
            return self.packages_[name]
        return None

    @property
    def nodes(self):
        return self.vms_

    def setup_hosts(self):
        hosts = ""
        for node in self.nodes:
            hosts = hosts + "\n" + "{0}\t{1}".format(node.intf_ip('eth0'), node.name)
        parallel(lambda vm: vm.script(write_template('etc-hosts', '/etc/hosts', hosts=hosts)), self.nodes)

    def setup_hostnames(self):
        parallel(lambda vm: vm.script("echo {name} | sudo tee /etc/hostname".format(name=vm.name)), self.nodes)
        parallel(lambda vm: vm.script("sudo hostname {name}".format(name=vm.name)), self.nodes)

    def setup(self):
        self.setup_hostnames()
        self.setup_hosts()
        self.is_setup_ = True
