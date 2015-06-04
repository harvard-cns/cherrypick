import threading
import Queue
import subprocess
import fcntl
import os
import select


class Command:
    def __init__(self, ssh, command):
        self._ssh = ssh
        self._cmd = command.split(" ")
        self.start()

    def start(self):
        """
        Start the command by executing it on the remote ssh server.
        stdout and stderr are set to nonblocking so we can read off of
        the server while performing other operations
        """
        def nonblock(fd):
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        def run_cmd(ssh, command):
            print "Executing %s" % command
            print "Executing %s" % " ".join( ["ssh", "-t", "-t", ssh.vm(),
                '--'] + command)
            return subprocess.Popen(
                    ["ssh", "-t", "-t", ssh.vm(), '--'] + command,
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


    def vm(self):
        return self._vm

    def __lshift__(self, command):
        cmd = Command(self, command)
        self._commands.append(cmd)
        return cmd


q = SSH("omid@rumi") << "ping google.com -c4" << "echo whatever"
q.wait()
r = q.read()
while (r not in [None, ""]):
    print r
    r = q.read()
print r
print "Done waiting"
