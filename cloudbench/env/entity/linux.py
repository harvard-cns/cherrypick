from .behavior import SecureShell, RsyncTransfer, SecureShell
from .behavior import LinuxInstaller, LinuxFileSystem, FileSystem

from cloudbench.package_manager import AptManager

class Linux(RsyncTransfer, SecureShell, LinuxInstaller, LinuxFileSystem):
    def __init__(self, *args, **kwargs):
        print "Calling linux?"
        super(Linux, self).__init__(*args, **kwargs)

class Ubuntu(Linux):
    def __init__(self, *args, **kwargs):
        print "Calling ubuntu?"
        super(Ubuntu, self).__init__(*args, **kwargs)

    @property
    def package_manager(self):
        if not hasattr(self, 'pkgmgr_'):
            self.pkgmgr_ = AptManager(self)

        return self.pkgmgr_

LinuxFileSystem()
