class Cluster(object):
    def __init__(self, vms, user='cloudbench'):
        self.vms_ = vms
        self.user_ = user

    def setup_keys(self):
        # Get the virtual machine keys
        keys = map(lambda vm: vm.public_key(user=self.user_), self.vms_)

        # Command for adding a key to the list of authorized users
        cmd = """sudo su {0} -c cat <<EOT > /home/{0}/.ssh/authorized_keys
{1}
EOT"""

        disable_host_key_checking = """sudo su {0} -c cat <<EOT > /home/{0}/.ssh/config
Host *
    StrictHostKeyChecking=no
    UserKnownHostsFile=/dev/null
EOT"""
        

        # Maybe we can upload keys later on, instead of adding them one
        # by one ...
        for vm in self.vms_:
            vm.script(cmd.format(self.user_, "\n".join(keys)))

            # Also disable strict host key checking
            # http://stackoverflow.com/questions/1655815/ssh-on-linux-disabling-host-key-checking-for-hosts-on-local-subnet-known-hosts
            vm.script(disable_host_key_checking.format(self.user_))
