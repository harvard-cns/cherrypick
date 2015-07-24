from .behavior import SecureShell, RsyncTransfer, SecureShell
from .behavior import LinuxInstaller, LinuxFileSystem, FileSystem

from cloudbench.package_manager import AptManager

class Linux(RsyncTransfer, SecureShell, LinuxInstaller, LinuxFileSystem):
    def __init__(self, *args, **kwargs):
        super(Linux, self).__init__(*args, **kwargs)

    def intf_ip(self, intf='eth0'):
        extract = """grep -B1 "inet addr" |awk '{ if ( $1 == "inet" ) { print $2 }}' | awk -F: '{printf "%s", $2}'"""
        print("ifconfig " + intf + " | " + extract)
        return self.script("ifconfig " + intf + " | " + extract)

class Ubuntu(Linux):
    def __init__(self, *args, **kwargs):
        super(Ubuntu, self).__init__(*args, **kwargs)

    @property
    def package_manager(self):
        if not hasattr(self, 'pkgmgr_'):
            self.pkgmgr_ = AptManager(self)

        return self.pkgmgr_
