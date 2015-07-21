from threading import RLock
from cloudbench.ssh import Ssh, WaitUp
from cloudbench.rsync import Rsync

import inflection
import time

class Base(object):
    def __init__(self, *args, **kwargs):
        super(Base, self).__init__()

class SecureShell(Base):
    def __init__(self, *args, **kwargs):
        print "Calling secure shell"
        self._ssh = None
        super(SecureShell, self).__init__(*args, **kwargs)

    def ssh(self, new=False, waitUp=True):
        """ Return a SSH tunnel."""
        if new:
            return Ssh(self, "".join([self.username, '@', self.url]))

        if self._ssh:
            return self._ssh

        self._ssh = Ssh(self, "".join([self.username, '@', self.url]))
        return self._ssh

    def execute(self, command, daemon=False):
        ssh = self.ssh(new=True)
        cmd = (ssh << command)
        if daemon:
            return None

        cmd.wait()
        return cmd.read()

class Installer(Base):
    def __init__(self, *args, **kwargs):
        print "Calling installer"
        super(Installer, self).__init__(*args, **kwargs)

    def install(self, package):
        pass

    def installed(self, package):
        pass

    def remove(self, package):
        pass

class LinuxInstaller(Installer):
    def __init__(self, *args, **kwargs):
        print "Calling linux installer"
        super(LinuxInstaller, self).__init__(*args, **kwargs)

    def install(self, package):
        return self.module(package, 'install').install(self)

    def installed(self, package):
        return self.module(package, 'installed').installed(self)

    def remove(self, package):
        return self.module(package, 'remove').remove(self)

    def module(self, package, what):
        return __import__('cloudbench.apps.' + package, fromlist=[what])

class FileSystem(Base):
    class Cd(Base):
        def __init__(self, vm, directory):
            self.vm_ = vm
            self.dir_ = directory

        def execute(self, command):
            return self.vm_.execute('cd %s && %s' % (self.dir_, command))

        def __enter__(self):
            return self

        def __exit__(self, typ, value, traceback):
            pass

    def __init__(self, *args, **kwargs):
        print 'Calling Directory'
        super(FileSystem, self).__init__(*args, **kwargs)

    def mkdir(self, name):
        pass

    def rmdir(self, name):
        pass

    def cd(self, directory):
        return FileSystem.Cd(self, directory)

class LinuxFileSystem(FileSystem):
    def __init__(self, *args, **kwargs):
        print 'calling LinuxDirectory'
        print 'Directory: %s' % super(LinuxFileSystem, self)
        super(LinuxFileSystem, self).__init__(*args, **kwargs)

    def mkdir(self, name):
        return self.execute('mkdir %s' % name)

    def rmdir(self, name):
        return self.execute('rm -rf %s' % name)

class RsyncTransfer(Base):
    def __init__(self, *args, **kwargs):
        print 'Calling RsyncTransfer'
        super(RsyncTransfer, self).__init__(*args, **kwargs)

    def rsync(self):
        return Rsync(self, "".join([self.username, '@', self.url]))

    def send(self, what, where):
        client = self.rsync()
        client.send(what, where)
        client.wait()

    def recv(self, what, where):
        client = self.rsync()
        client.recv(what, where)
        client.wait()

class Preemptable(Base):
    def __init__(self, *args, **kwargs):
        super(Preemptable, self).__init__(*args, **kwargs)
        self._lock = RLock()

        # TODO: Azure ... is weird, we will always assume that the VMs
        #       are down.
        self._started = None
        self._stale = None

    def class_name(self):
        """ Returns the class name of the entity, e.g.:
        VirtualMachine -> 'virtual_machine'
        """
        return inflection.underscore(self.__class__.__name__)

    def wait(self, timeout=120):
        """ Wait for the VM to come up """
        if self.stale is not None:
            return self.stale

        cmd = WaitUp(cmd='exit', timeout=timeout)
        if cmd.start(self.ssh()):
            self._stale = False
            return True

        self._stale = True
        return self._stale

    @property
    def stale(self):
        return self._stale

    def start(self):
        """ Ask the cloud factory for a boot up """
        with self._lock:
            if not self.started():
                self._started = None
                getattr(self.factory, 'start_' + self.class_name())(self)

    def stop(self):
        """ Stop the entity if it has started """
        with self._lock:
            if not self.stopped():
                self._started = None
                getattr(self.factory, 'stop_' + self.class_name())(self)

    def started(self):
        """ Returns true if the entity has started """
        if self._started is not None:
            return self._started

        self._started = getattr(self.factory, 'status_' + self.class_name())(self)
        return self._started

    def stopped(self):
        """ Returns true if the entity has stopped """
        if self._started is not None:
            return not self._started

        self._started = getattr(self.factory, 'status_' + self.class_name())(self)

        if self._started is not None:
            return not self._started
        return None

    def reset(self):
        """ Ask the cloud factory for a reset """
        self.stop()
        self.start()
