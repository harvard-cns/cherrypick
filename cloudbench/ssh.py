import threading
import Queue
import subprocess
import fcntl
import os
import select
import sys
import time

DEBUG=False

class Command(object):
    def __init__(self, command):
        self._ssh = None
        self._cmd = command.split(" ")

    def start(self, ssh):
        """
        Start the command by executing it on the remote ssh server.
        stdout and stderr are set to nonblocking so we can read off of
        the server while performing other operations
        """
        self._ssh = ssh

        def nonblock(fd):
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        def run_cmd(ssh, command):
            if DEBUG:
                print "Executing %s" % " ".join( ["ssh",
                    "-oStrictHostKeyChecking=no", "-t", "-t", ssh.vm(),
                    '--'] + command)

            return subprocess.Popen(
                    ["ssh", "-oStrictHostKeyChecking=no", "-t", "-t",
                        ssh.vm(), '--'] + command,
                    stderr=subprocess.PIPE, stdout=subprocess.PIPE)

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
                        if (r == ""): return True
                        queue.put(r)
                    except Exception as e:
                        raise e


        self._process = run_cmd(self._ssh, self._cmd)
        self._queue   = Queue.Queue()

        self._thread  = threading.Thread(
                target=monitor_process,
                args=(self._process, self._queue,))

        self._thread.start()

    def wait(self):
        self._thread.join()
        return self

    def terminate(self):
        # Check if the process has already terminated
        if self._process.poll() is not None:
            return self

        self._process.terminate()
        self.wait()
        return self

    def read(self):
        if not self._queue.empty():
            return self._queue.get(False)

        return None

    def __lshift__(self, cmd):
        return (self._ssh << cmd)


class WaitUntilFinished(Command):
    def start(self, ssh):
        super(WaitUntilFinished, self).start(ssh)
        self.wait()

class WaitForSeconds(Command):
    def __init__(self, command, time):
        super(WaitForSeconds, self).__init__(command)
        self._time = time

    def start(self, ssh):
        super(WaitForSeconds, self).start(ssh)
        time.sleep(self._time)

"""
A nonblocking SSH tunnel which allows for executing arbitrary commands.
It is possible to wait for the chain of commands to finish.  All the
outputs are also logged and can be accessed for the purpose of
benchmark: preparing the VM, execution of benchmark, and tearing down
the VM
"""
class SSH:
    def __init__(self, vm):
        self._commands = []
        self._vm = vm
        self._ip = None

    def vm(self):
        return self._vm

    def ip(self):
        if not self._ip:
            q = self << WaitUntilFinished("curl ifconfig.me")
            self._ip = q.read().strip()
        return self._ip 

    def last_command(self):
        if not self._commands:
            return self

        return self._commands[-1]

    def __lshift__(self, cmd):
        if not isinstance(cmd, Command):
            cmd = Command(cmd)
        self._commands.append(cmd)
        cmd.start(self)
        return cmd

    def read(self):
        if self.last_command() != self:
            return self.last_command().read()
        return None

    def terminate(self):
        map(lambda c: c.terminate(), self._commands)
        return self

