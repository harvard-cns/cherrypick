from threading import RLock
from cloudbench.ssh import Ssh, WaitUp

import inflection
import time

class SecureShell(object):
    def __init__(self, *args, **kwargs):
        super(SecureShell, self).__init__(*args, **kwargs)
        self._ssh = None

    def ssh(self, new=False, waitUp=True):
        """ Return a SSH tunnel."""
        if new:
            return Ssh(self, "".join([self.username, '@', self.url]))

        if self._ssh:
            return self._ssh

        self._ssh = Ssh(self, "".join([self.username, '@', self.url]))
        return self._ssh

class Preemptable(object):
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
