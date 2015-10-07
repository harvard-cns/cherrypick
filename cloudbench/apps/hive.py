from .hadoop import HADOOP_USER, HADOOP_GROUP, HADOOP_PSWD, HADOOP_DIR

HIVE_SOURCE='http://apache.arvixe.com/hive/hive-1.2.1/apache-hive-1.2.1-bin.tar.gz'
HIVE_PATH='/usr/local/hive'

HIVE_CONFIG="""sudo su {0} -c cat <<EOT >> /home/{0}/.profile
export HIVE_HOME="{1}"
export PATH=\$PATH:\$HIVE_HOME/bin
EOT
""".format(HADOOP_USER, HIVE_PATH)

HIVE_CONFIG_DIR=""" sudo su {0} -c cat <<EOT >> {1}/bin/hive-config.sh
export HADOOP_HOME="{2}"
EOT
""".format(HADOOP_USER, HIVE_PATH, HADOOP_DIR)

HIVE_SITE_CONFIG="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
<property>
    <name>hive.mapjoin.smalltable.filesize</name>
    <value>128000000</value>
</property>
<property>
    <name>hive.auto.convert.join.noconditionaltask.size</name>
    <value>5000000</value>
</property>
</configuration>
"""

def modify_hive_config(config, f):
    command = "sudo su - {0} -c cat <<EOT > {1}{2}\n{3}\nEOT"
    command = command.format(HADOOP_USER, HIVE_PATH, f, config)
    return command

def get_hive(vm):
    vm.script('wget -rc -nd -q "{0}"'.format(HIVE_SOURCE))
    vm.script('tar -xzf apache-hive-1.2.1-bin.tar.gz')
    vm.script('rm -rf {0}'.format(HIVE_PATH))
    vm.script('mv apache-hive-1.2.1-bin {0}'.format(HIVE_PATH))
    vm.script('chown -R {0}:{1} {2}'.format(HADOOP_USER, HADOOP_GROUP, HIVE_PATH))

def setup_hive_site(vm):
    modify_hive_config(
        HIVE_SITE_CONFIG, '/conf/hive-site.xml')


def setup_hive(vm):
    vm.script(HIVE_CONFIG)
    vm.script(HIVE_CONFIG_DIR)

def install(vm):
    get_hive(vm)
    setup_hive(vm)

def uninstall(vm):
    pass
