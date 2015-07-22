class Cluster(object):
    def __init__(vms, user='cloudbench'):
        self.vms_ = vms

    def setup_keys(self):
        # Get the virtual machine keys
        keys = map(lambda vm: vm.public_key(), self.vms_)

        # Command for adding a key to the list of authorized users
        cmd = 'sudo su {0} -c "echo {1} >> /home/{0}/.ssh/authorized_keys"'

        # Maybe we can upload keys later on, instead of adding them one
        # by one ...
        for vm in self.vms_:
            for key in keys:
                vm.execute(cmd.format(self.user_, key))

        # Also disable strict host key checking
        # http://stackoverflow.com/questions/1655815/ssh-on-linux-disabling-host-key-checking-for-hosts-on-local-subnet-known-hosts

