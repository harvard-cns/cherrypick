HADOOP_USER='hduser'
HADOOP_GROUP='hadoop'
HADOOP_PSWD='hadoop123'
HADOOP_DIR='/usr/local/hadoop'

def create_user(vm):
    vm.execute('sudo addgroup %s' % HADOOP_GROUP)
    vm.execute('sudo adduser --ingroup hadoop --disabled-password --shell /bin/bash --home /home/hduser --gecos "HDUser" --quiet %s' % HADOOP_USER)
    vm.execute("\"echo '%s:%s' | sudo chpasswd\"" % (HADOOP_USER, HADOOP_PSWD))
    vm.execute("sudo su {0} -c 'ssh-keygen -t rsa -q -f/home/{0}/.ssh/id_rsa -N \"\" -q'".format(HADOOP_USER))
    vm.execute("'sudo su {0} -c \"cat /home/{0}/.ssh/id_rsa.pub >> /home/{0}/.ssh/authorized_keys\"'".format(HADOOP_USER))


def get_hadoop(vm):
    vm.execute("wget -rc -nd \"http://apache.mirrors.pair.com/hadoop/core/hadoop-2.7.1/hadoop-2.7.1.tar.gz\"")
    vm.execute("tar -xzf hadoop-2.7.1.tar.gz")
    vm.execute("sudo mkdir -p %s" % HADOOP_DIR)
    vm.execute("sudo mv hadoop-2.7.1/* %s" % HADOOP_DIR)
    vm.execute("sudo chown -R %s:%s /usr/local/hadoop/" % (HADOOP_USER, HADOOP_GROUP))

def setup_user_env(vm):
    bash_env = """export JAVA_HOME=/usr/lib/jvm/java-8-oracle
export HADOOP_INSTALL={0}
export PATH=\\\\$PATH:\\\\$HADOOP_INSTALL/bin
export PATH=\\\\$PATH:\\\\$HADOOP_INSTALL/sbin
export HADOOP_MAPRED_HOME=\\\\$HADOOP_INSTALL
export HADOOP_COMMON_HOME=\\\\$HADOOP_INSTALL
export HADOOP_HDFS_HOME=\\\\$HADOOP_INSTALL
export YARN=\\\\$HADOOP_INSTALL
export HADOOP_COMMON_LIB_NATIVE_DIR=\\\\$HADOOP_INSTALL/lib/native
export HADOOP_OPTS=\\\\"-Djava.library.path=\\\\$HADOOP_INSTALL/lib/native\\\\" """
    bash_env = bash_env.format(HADOOP_DIR)

    if not vm.execute("'sudo su {0} -c \"cat /home/{0}/.bashrc | grep HADOOP_OPTS\"'".format(HADOOP_USER)):
        for line in bash_env.split("\n"):
            vm.execute("\"sudo su {0} -c 'echo {1} >> /home/{0}/.bashrc'\"".format(HADOOP_USER, line))

def install(vm):
    vm.install('java8')
    create_user(vm)
    get_hadoop(vm)
    setup_user_env(vm)
