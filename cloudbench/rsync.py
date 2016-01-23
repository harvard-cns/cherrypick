import shlex
import subprocess
import threading

class Rsync(object):
    def __init__(self, vm, connect_string):
        self._vm = vm
        self._connect_string = connect_string
        self._process = None
        self._lock = threading.RLock()

    @property
    def vm(self):
        return self._vm

    @property
    def connect_string(self):
        """
        Returns the virtual machine, for now this is just th string that
        SSH clients use to connect to the server, e.g., username@domain
        """
        return self._connect_string

    def send(self, source, dest):
        """ Sends the source directory to the destination directory """
        self._lock.acquire()
        self._process = subprocess.Popen(shlex.split(
            "rsync -avz -e 'ssh -i ../config/cloud.key -oStrictHostKeyChecking=no -q' {0} {1}:{2}".format(
                    source, self.connect_string, dest)), 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def recv(self, source, dest):
        self._lock.acquire()
        print("rsync -avz -e 'ssh -i ../config/cloud.key -oStrictHostKeyChecking=no -q' {0}:{1} {2}".format(self.connect_string, source , dest))
        self._process = subprocess.Popen(shlex.split(
            "rsync -avz -e 'ssh -i ../config/cloud.key -oStrictHostKeyChecking=no -q' {0}:{1} {2}".format(
                    self.connect_string, source , dest)), 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def wait(self):
        stdout, stderr = self._process.communicate()

        try:
            self._process.stdout.close()
            self._process.stderr.close()
        except Exception:
            pass

        if self._process.poll() is None:
            self._process.terminate()
        self._process = None
        self._lock.release()
        return (stdout, stderr)
