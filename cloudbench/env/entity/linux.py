from .behavior import SecureShell, RsyncTransfer, SecureShell
from .behavior import LinuxInstaller, LinuxFileSystem, FileSystem

from cloudbench.package_manager import AptManager

class Linux(RsyncTransfer, SecureShell, LinuxInstaller, LinuxFileSystem):
    def __init__(self, *args, **kwargs):
        super(Linux, self).__init__(*args, **kwargs)

        self._memory = None;
        self._cpus = None;

    def intf_ip(self, intf='eth0'):
        extract = """grep -B1 "inet addr" |awk '{ if ( $1 == "inet" ) { print $2 }}' | awk -F: '{printf "%s", $2}'"""
        return self.script("ifconfig " + intf + " | " + extract)

    def memory(self):
        if not self._memory:
            self._memory = int(self.script("cat /proc/meminfo | grep MemTotal | awk '{ print $2 }'"))
        return self._memory * 1024

    def cpus(self):
        if not self._cpus:
            nproc_out = self.script("nproc")
            self._cpus = int(nproc_out)
        return self._cpus

    def root_disk(self):
        return self.script("df -P / | tail -n 1 | awk '/.*/ { print $1 }'")

    def disks(self):
        return filter(lambda x: not x.endswith(('a','b','c','d','e')),
                    filter(lambda x: x.startswith('/dev/'),
                        self.script("ls /dev/{sd,xvd}* 2>/dev/null | grep -v 1").split("\n")))

    def local_disks_except_root(self):
        return filter(lambda x: not x.endswith(('a')),
                    filter(lambda x: x.startswith('/dev/'),
                        self.script("ls /dev/{sd,xvd}* 2>/dev/null | grep -v 1").split("\n")))

    def all_disks_except_root(self):
        return filter(lambda x: not x.endswith(('a')),
                    filter(lambda x: x.startswith('/dev/'),
                        self.script("ls /dev/{sd,xvd}* 2>/dev/null | grep -v 1").split("\n")))

    def has_dir(self, path):
        output = self.script("if [ -d \"%s\" ]; then echo true; else echo false; fi" % path)
        if output.strip() == 'true':
            return True
        return False

    def mount(self, disk, path, disk_format='ext3', force_format=False):
        partition = disk + '1'
        if force_format:
            self.script('umount %s' % disk)
            self.script('umount %s1' % disk)
            self.script('(echo o; echo n; echo p; echo 1; echo; echo; echo w) | sudo fdisk %s' % disk)
            self.script('partprobe')
            self.script('sudo mkfs.%s %s' % (disk_format, partition))
        self.script('mkdir -p %s' % path)
        self.script('umount %s' % path)
        self.script('mount %s %s' % (partition, path))

class Ubuntu(Linux):
    def __init__(self, *args, **kwargs):
        super(Ubuntu, self).__init__(*args, **kwargs)

    @property
    def package_manager(self):
        if not hasattr(self, 'pkgmgr_'):
            self.pkgmgr_ = AptManager(self)

        return self.pkgmgr_
