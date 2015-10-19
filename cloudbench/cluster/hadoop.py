from .base import Cluster
from cloudbench.apps.hadoop import HADOOP_USER, HADOOP_DIR, HADOOP_GROUP
from cloudbench.util import parallel

# The instruction is taken from:
# https://chawlasumit.wordpress.com/2015/03/09/install-a-multi-node-hadoop-cluster-on-ubuntu-14-04/
def bytes2mega(size):
    return size/(1024*1024)

CoreSiteTemplate="""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
{0}
</configuration>
"""

MapRedSiteTemplate="""<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
{0}
</configuration>
"""

HdfsSiteTemplate="""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
{0}
</configuration>
"""

YarnSiteTemplate="""<?xml version="1.0"?>
<configuration>
{0}
</configuration>
"""

EtcHostsTemplate="""
127.0.0.1\tlocalhost
{0}
"""

Ports=[54310, 54311, ]

def modify_hadoop_config(config, f):
    command = "sudo su - {0} -c cat <<EOT > {1}{2}\n{3}\nEOT"
    command = command.format(HADOOP_USER, HADOOP_DIR, f, config)
    return command

class HadoopCluster(Cluster):
    def __init__(self, master_, slaves_, local_disk_=True):
        self.master = master_
        self.slaves_ = slaves_
        self.local_disk_ = local_disk_

        super(HadoopCluster, self).__init__(self.all_nodes(), HADOOP_USER)

        def setup_hdfs_permissions(vm):
            path = self.hdfs_path(vm)
            if 'home' not in path:
                vm.mount('/dev/xvdb', path, 'ext4', True)
                vm.script('chown -R %s:%s %s' % (HADOOP_USER, HADOOP_GROUP, path))
                vm.script("chmod -R 755 %s" % path)

        parallel(setup_hdfs_permissions, self.all_nodes())

    def hdfs_path(self, vm):
        if self.use_local_disk:
            return '/hadoop-data'
        else:
            return '/home/%s' % HADOOP_USER

    @property
    def use_local_disk(self):
        return self.local_disk_

    @property
    def master(self):
        return self.master_

    @master.setter
    def master(self, value):
        self.master_ = value

    def master_ip(self):
        return self.master_.intf_ip('eth0')

    @property
    def slaves(self):
        return self.slaves_

    @slaves.setter
    def slaves(self, slaves):
        self.slaves_ = slaves


    def setup_core_site(self):
        config = """
           <property>
             <name>hadoop.tmp.dir</name>
             <value>file://{0}/tmp</value>
             <description>Temporary Directory.</description>
           </property>

           <property>
             <name>fs.defaultFS</name>
             <value>hdfs://{1}:54310</value>
             <description>Use HDFS as file storage engine</description>
           </property> 
        """

        config = CoreSiteTemplate.format(config.format(self.hdfs_path(self.master), self.master.name))
        command = modify_hadoop_config(config, '/etc/hadoop/core-site.xml')
    
        # Upload the file in parallel
        parallel(lambda node: node.script(command), self.all_nodes())

    def all_nodes(self):
        return list(set([self.master] + self.slaves))

    def mapred_config(self, vm):
        config = """
<property>
    <name>mapreduce.jobhistory.webapp.address</name>
    <value>0.0.0.0:19888</value>
</property>
<property>
    <name>mapreduce.jobhistory.address</name>
    <value>0.0.0.0:10020</value>
</property>
<property>
    <name>mapreduce.jobhistory.intermediate-done-dir</name>
    <value>/home/hduser/mr-history/tmp</value>
</property>
<property>
    <name>mapreduce.jobhistory.done-dir</name>
    <value>/home/hduser/mr-history/done</value>
</property>
<property>
 <name>mapreduce.jobtracker.address</name>
 <value>{0}:54311</value>
 <description>The host and port that the MapReduce job tracker runs
  at. If "local", then jobs are run in-process as a single map
  and reduce task.
</description>
</property>
<property>
 <name>mapreduce.framework.name</name>
 <value>yarn</value>
 <description>The framework for running mapreduce jobs</description>
</property>
<property>
  <name>mapreduce.map.memory.mb</name>
  <value>{1}</value>
</property>
<property>
  <name>mapreduce.reduce.memory.mb</name>
  <value>{2}</value>
</property>
<property>
  <name>mapreduce.map.java.opts</name>
  <value>-Xmx{3}m</value>
</property>
<property>
  <name>mapreduce.reduce.java.opts</name>
  <value>-Xmx{4}m</value>
</property>
"""
        map_size = int((bytes2mega(vm.memory()) - 1024) / (vm.cpus() * 2))
        red_size = int((bytes2mega(vm.memory()) - 1024) / (vm.cpus() * 1))
        
        map_heap_size = map_size * 3 / 4
        red_heap_size = red_size * 3 / 4

        config = MapRedSiteTemplate.format(
                config.format(self.master.name, map_size, red_size,
                    map_heap_size, red_heap_size))

        return modify_hadoop_config(config, '/etc/hadoop/mapred-site.xml')

    def setup_mapred_site(self):
        self.master.script(self.mapred_config(self.master))

    def setup_hdfs_site(self):
        dirs = ["{0}/hdfs/datanode", "{0}/hdfs/namenode"]
        def create_hdfs_dirs(vm):
            for d in map(lambda x: x.format(self.hdfs_path(vm)), dirs):
                vm.script('sudo su - {0} -c "mkdir -p {1}"'.format(HADOOP_USER, d))

        parallel(create_hdfs_dirs, self.all_nodes())

        config = """
<property>
 <name>dfs.replication</name>
 <value>1</value>
 <description>Default block replication.
  The actual number of replications can be specified when the file is created.
  The default is used if replication is not specified in create time.
 </description>
</property>
<property>
 <name>dfs.namenode.name.dir</name>
 <value>{0}/hdfs/namenode</value>
 <description>Determines where on the local filesystem the DFS name node should store the name table(fsimage). If this is a comma-delimited list of directories then the name table is replicated in all of the directories, for redundancy.
 </description>
</property>
<property>
 <name>dfs.datanode.data.dir</name>
 <value>{0}/hdfs/datanode</value>
 <description>Determines where on the local filesystem an DFS data node should store its blocks. If this is a comma-delimited list of directories, then data will be stored in all named directories, typically on different devices. Directories that do not exist are ignored.
 </description>
</property>
"""
        config = HdfsSiteTemplate.format(config.format(self.hdfs_path(self.master)))
        command = modify_hadoop_config(config, '/etc/hadoop/hdfs-site.xml')
        parallel(lambda vm: vm.script(command), self.all_nodes())

    def yarn_config(self, vm):
        config = """
<property>
 <name>yarn.nodemanager.aux-services</name>
 <value>mapreduce_shuffle</value>
</property>
<property>
  <name>yarn.nodemanager.aux-services.mapreduce_shuffle.class</name>
  <value>org.apache.hadoop.mapred.ShuffleHandler</value>
</property>
<property>
 <name>yarn.resourcemanager.scheduler.address</name>
 <value>{0}:8030</value>
</property> 
<property>
 <name>yarn.resourcemanager.address</name>
 <value>{0}:8032</value>
</property>
<property>
  <name>yarn.resourcemanager.webapp.address</name>
  <value>{0}:8088</value>
</property>
<property>
  <name>yarn.resourcemanager.resource-tracker.address</name>
  <value>{0}:8031</value>
</property>
<property>
  <name>yarn.resourcemanager.admin.address</name>
  <value>{0}:8033</value>
</property>
<property>
  <name>yarn.nodemanager.resource.memory-mb</name>
  <value>{1}</value>
</property>
<property>
  <name>yarn.scheduler.minimum-allocation-mb</name>
  <value>{2}</value>
</property>
<property>
  <name>yarn.resourcemanager.hostname</name>
  <value>{0}</value>
</property>
<property>
   <name>yarn.nodemanager.vmem-pmem-ratio</name>
   <value>5</value>
   <description>Ratio between virtual memory to physical memory when setting memory limits for containers</description>
</property>
"""
        total_mem_size = bytes2mega(vm.memory()) - 1024
        min_mem_size   = total_mem_size / (vm.cpus()*3)
        #min_mem_size   = total_mem_size / (vm.cpus())

        config = YarnSiteTemplate.format(
                config.format(self.master.name, total_mem_size, min_mem_size)) 

        print "-"*80
        print "-"*80
        print config
        print "-"*80
        return modify_hadoop_config(config, '/etc/hadoop/yarn-site.xml')

    def setup_yarn_site(self):
        parallel(lambda vm: vm.script(self.yarn_config(vm)), self.all_nodes())

    def setup_slaves(self):
        hosts = ""
        names = set()
        for node in self.all_nodes():
            hosts = hosts + "\n" + "{0}\t{1}".format(node.intf_ip('eth0'), node.name)
            names.add(node.name)

        for node in self.all_nodes():
            command = "sudo cat <<EOT > /etc/hosts\n{0}\nEOT"
            node.script(command.format(EtcHostsTemplate.format(hosts)))
            node.script('sudo hostname {0}'.format(node.name))
            node.script('echo \'echo {0} > /etc/hostname\' | sudo bash'.format(node.name))

        config = "\n".join(list(names))
        command = modify_hadoop_config(config, '/etc/hadoop/slaves')
        self.master.script(command)

    def setup(self):
        self.setup_keys()
        self.setup_core_site()
        self.setup_mapred_site()
        self.setup_hdfs_site()
        self.setup_yarn_site()
        self.setup_slaves()

    def reset(self):
        self.format_hdfs()
        self.restart_dfs()
        self.restart_yarn()
        self.restart_job_history()

    def hadoop_user_cmd(self, cmd):
        return 'sudo su - {0} -c {1}'.format(HADOOP_USER, cmd)

    def start_job_history(self):
        start_jh = self.hadoop_user_cmd('"mr-jobhistory-daemon.sh start historyserver"')
        parallel(lambda vm: vm.script(start_jh), self.all_nodes())

    def stop_job_history(self):
        stop_jh = self.hadoop_user_cmd('"mr-jobhistory-daemon.sh stop historyserver"')
        parallel(lambda vm: vm.script(stop_jh), self.all_nodes())

    def restart_job_history(self):
        self.stop_job_history()
        self.start_job_history()

    def start_dfs(self):
        self.master.script(
                self.hadoop_user_cmd('"start-dfs.sh"'))

    def stop_dfs(self):
        self.master.script(
                self.hadoop_user_cmd('"stop-dfs.sh"'))

    def restart_dfs(self):
        self.stop_dfs()
        self.start_dfs()

    def start_yarn(self):
        self.master.script(
                self.hadoop_user_cmd('"start-yarn.sh"'))

    def stop_yarn(self):
        self.master.script(
                self.hadoop_user_cmd('"stop-yarn.sh"'))

    def restart_yarn(self):
        self.stop_yarn()
        self.start_yarn()

    def format_hdfs(self):
        remove_hdfs_dir = self.hadoop_user_cmd('"rm -rf {0}/hdfs"'.format(self.hdfs_path(self.master)))
        parallel(lambda vm: vm.script(remove_hdfs_dir), self.all_nodes())

        remove_hdfs_dir = self.hadoop_user_cmd('"rm -rf {0}/tmp"'.format(self.hdfs_path(self.master)))
        parallel(lambda vm: vm.script(remove_hdfs_dir), self.all_nodes())

        self.master.script(
                self.hadoop_user_cmd('"hdfs namenode -format -force"'))

    def execute(self, cmd):
        return self.master.script(
                self.hadoop_user_cmd(cmd))
