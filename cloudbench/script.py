from ssh import SSH, WaitForSeconds, WaitUntilFinished
import sys

vm1ssh = SSH("omid@rumi")
vm2ssh = SSH("omid@mm")

vm1ssh << WaitForSeconds("iperf -s", 3)
vm2ssh << WaitUntilFinished("iperf -y c -c " + vm1ssh.ip())

print "Reading vm2: "
print vm2ssh.read()

vm1ssh.terminate()
vm2ssh.terminate()
