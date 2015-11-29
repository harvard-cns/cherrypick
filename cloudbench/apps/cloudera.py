CLOUDERA_APTGET_PRIORITY="""cat <<EOT | sudo tee /etc/apt/preferences.d/cloudera.pref
Package: *
Pin: release o=Cloudera, l=Cloudera
Pin-Priority: 501
EOT"""

def install(vm):
    vm.script("sudo wget 'https://archive.cloudera.com/cdh5/ubuntu/trusty/amd64/cdh/cloudera.list' -O /etc/apt/sources.list.d/cloudera.list")
    vm.script(CLOUDERA_APTGET_PRIORITY)
    vm.script("sudo wget https://archive.cloudera.com/cdh5/ubuntu/trusty/amd64/cdh/archive.key -O archive.key")
    vm.script("sudo apt-key add archive.key")
    vm.script("sudo apt-get update")

def uninstall(vm):
    pass

def installed(vms):
    pass


