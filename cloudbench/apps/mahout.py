from .hadoop import HADOOP_USER, HADOOP_GROUP, HADOOP_PSWD, HADOOP_DIR
MAHOUT_PATH="/usr/local/mahout"

MAHOUT_CONFIG="""sudo su {0} -c cat <<EOT >> /home/{0}/.profile
export MAHOUT_HOME="{1}"
export PATH=\$PATH:\$MAHOUT_HOME/bin
EOT
""".format(HADOOP_USER, MAHOUT_PATH)


def install(vm):
    vm.script("wget -rc -nd -q http://apache.arvixe.com/mahout/0.11.0/apache-mahout-distribution-0.11.0.tar.gz")
    vm.script("tar -xzf apache-mahout-distribution-0.11.0.tar.gz")
    vm.script("rm -rf {0}".format(MAHOUT_PATH))
    vm.script("mv apache-mahout-distribution-0.11.0 {0}".format(MAHOUT_PATH))
    vm.script("chown -R {0}:{1} {2}".format(HADOOP_USER, HADOOP_GROUP, MAHOUT_PATH))
    vm.script(MAHOUT_CONFIG)
