import fcntl
import os
import Queue
import select
import shlex
import signal
import subprocess
import sys
import threading
import time

import constants

from util import Debug

class Command(object):
    """A Command object is a SSH process that is getting executed on the
    remoted server.

    For each command object, a separate thread reads the output of the
    remote process periodically and adds it to a thread-safe queue that
    can be accessed in other places
    """
    def __init__(self, command):
        self._ssh = None
        self._cmd = command

    def start(self, ssh):
        """Start the command by executing it on a remote ssh server.

        stdout and stderr are set to nonblocking so we can read off of
        the server while performing other operations.  This method
        creates a thread that reads off data from the stdout and pushes
        them to a queue.  The queue can be accessed by using the read()
        method.
        """
        self._ssh = ssh

        def nonblock(fd):
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        def run_cmd(ssh, command, private_key = constants.DEFAULT_VM_PRIVATE_KEY):
            cmd = "ssh -i {} -q -o StrictHostKeyChecking=no "\
                   "{} -- {}".format(private_key,
                   ssh.connect_string, command)
            Debug.cmd << cmd << "\n"

            return subprocess.Popen(shlex.split(cmd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

        def monitor_process(p, queue):
            nonblock(p.stdout)
            nonblock(p.stderr)

            while (True):
                read, _, _ = select.select([p.stdout], [], [], 1)
                if read:
                    r = p.stdout.read(4096)
                    queue.put(r)

                # Check if the process is dead
                if p.poll() is None:
                    continue

                # If the process is dead just read as much data as we
                # can and then terminate the thread
                while (True):
                    try:
                        r = p.stdout.read(4096)
                        if (r == ""):
                            p.stdout.close()
                            p.stderr.close()
                            return True
                        queue.put(r)
                    except Exception as e:
                        print e
                        raise e


        self._process = run_cmd(self._ssh, self._cmd)
        self._queue   = Queue.Queue()

        self._thread  = threading.Thread(
                target=monitor_process,
                args=(self._process, self._queue,))
        self._thread.daemon = True
        self._thread.start()

    def process(self):
        return self._process

    def wait(self, timeout=None):
        """ Wait until the command has finished executing or an error
        occured in the thread."""
        self._thread.join(timeout)
        return self

    def terminate(self):
        """ Terminate the command gracefully """
        # Check if the process has already terminated
        if self._process.poll() is not None:
            return self

        self._process.send_signal(signal.SIGTERM)
        self.wait()
        return self

    def read(self):
        ret = ''
        while True:
            if self._queue.empty(): return ret
            ret += self._queue.get(False)

    def __lshift__(self, cmd):
        """ Pushes the next command to the SSH tunnel """
        return self._ssh << cmd


class WaitUntilFinished(Command):
    def start(self, ssh):
        """ Start executing the command, and wait until the command is
        finished executing """
        super(WaitUntilFinished, self).start(ssh)
        self.wait()

class WaitForSeconds(Command):
    def __init__(self, command, _time):
        super(WaitForSeconds, self).__init__(command)
        self._time = _time

    def start(self, ssh):
        """ Start the command and wait self._time seconds before
        proceeding to run the rest of the program.

        This is useful for programs that need coordination, or you just
        want to make sure that a process has started executing on the
        remote server before moving on.
        """
        super(WaitForSeconds, self).start(ssh)
        time.sleep(self._time)


class WaitUp(Command):
    def __init__(self, cmd='exit', timeout=120):
        super(WaitUp, self).__init__(cmd)
        self._timeout = timeout

    def start(self, ssh):
        Debug.info << "Waiting for %s " % ssh.connect_string
        start = time.time()
        while True:
            super(WaitUp, self).start(ssh)
            self.wait(self._timeout)

            if (time.time() - start) >= self._timeout:
                return False

            if self.process().poll() == 0:
                Debug.info << ("\n")
                Debug.info  << "%s is up.\n" % ssh.connect_string
                return True
            Debug.info << ('.')
            time.sleep(1)

"""
A nonblocking SSH tunnel which allows for executing arbitrary commands.
It is possible to wait for the chain of commands to finish.  All the
outputs are also logged and can be accessed for the purpose of
benchmark: preparing the VM, execution of benchmark, and tearing down
the VM
"""
class Ssh(object):
    def __init__(self, vm, connect_string):
        self._commands = []
        self._connect_string = connect_string
        self._vm  = vm
        self._ip = None

    @property
    def connect_string(self):
        """
        Returns the virtual machine, for now this is just th string that
        SSH clients use to connect to the server, e.g., username@domain
        """
        return self._connect_string

    def last_command(self):
        """
        Returns the last command that was executed on the remote server
        """
        if not self._commands:
            return self

        return self._commands[-1]

    def __lshift__(self, cmd):
        """
        Operator for piping data to the remote server
        """
        if not isinstance(cmd, Command):
            cmd = Command(cmd)
        self._commands.append(cmd)
        cmd.start(self)
        return cmd

    def read(self):
        """Read off the queue of the LAST command

        Since the commands are executed asynchronously there is no total
        order when the outputs are written, so it doesn't make sense to
        return anything but the last command.
        """
        if self.last_command() != self:
            return self.last_command().read()
        return None

    def terminate(self):
        """
        Terminates all the commands that are being executed on the remote
        server.  Useful for terminating a benchmark.
        """
        map(lambda c: c.terminate(), self._commands)
        return self

