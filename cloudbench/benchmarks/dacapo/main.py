from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

import datetime
import re
import time

TIMEOUT=30000000

BENCHMARK_SCRIPT="""
START=$(date +%s.%N)
java -jar dacapo-9.12-bach.jar avrora -s large
java -jar dacapo-9.12-bach.jar batik -s large
java -jar dacapo-9.12-bach.jar eclipse -s large
java -jar dacapo-9.12-bach.jar fop -s default
java -jar dacapo-9.12-bach.jar h2 -s default
java -jar dacapo-9.12-bach.jar jython -s large
java -jar dacapo-9.12-bach.jar luindex -s default
java -jar dacapo-9.12-bach.jar lusearch -s large
java -jar dacapo-9.12-bach.jar pmd -s large
java -jar dacapo-9.12-bach.jar sunflow -s large
java -jar dacapo-9.12-bach.jar tomcat -s huge
java -jar dacapo-9.12-bach.jar tradebeans -s huge
java -jar dacapo-9.12-bach.jar tradesoap -s huge
java -jar dacapo-9.12-bach.jar xalan -s large
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo $DIFF > out.txt
"""

BENCHMARK_SCRIPT="""
START=$(date +%s.%N)
java -jar dacapo-9.12-bach.jar avrora -s large
java -jar dacapo-9.12-bach.jar xalan -s large
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo $DIFF > out.txt
"""


def dacapo_for_vm(vm):
    vm.install('dacapo')
    #vm.script(BENCHMARK_SCRIPT)
    ts = time.time()
    fname = vm.name + '-' + str(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S'))
    vm.recv("~/out.txt", fname)

def dacapo_test(vms, env):
    parallel(dacapo_for_vm, vms)

def run(env):
    vms = []
    vms = map(lambda vm_name: env.vm(vm_name), env.virtual_machines())

    env.benchmark.executor(vms, dacapo_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

