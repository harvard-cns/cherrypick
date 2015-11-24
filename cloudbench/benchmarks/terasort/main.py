from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.hadoop import HADOOP_USER
from cloudbench.cluster.hadoop import HadoopCluster
from cloudbench.cluster.hive import HiveCluster

import re
import time

TIMEOUT=21600

TERASORT_INPUT='/home/{0}/terasort-input'.format(HADOOP_USER)
TERASORT_OUTPUT='/home/{0}/terasort-output'.format(HADOOP_USER)

COLLECT_TERASORT_SCRIPT="""
baseUrl="localhost:19888/ws/v1/history/mapreduce/jobs"
jobId=`curl $baseUrl 2>/dev/null | jq '.jobs.job[] | select (.name == "TeraSort") | .["id"]' | sed -e 's/"//g'`

jobUrl="${baseUrl}/$jobId"
tasksUrl="$jobUrl/tasks"
tasks=`curl $tasksUrl 2>/dev/null | jq '.tasks.task[] | .["id"]' | sed -e 's/"//g'`

output=""
for task in $tasks; do
        data=$(curl ${tasksUrl}/${task}/attempts 2>/dev/null)
        output="${data}\\n${output}"
done

echo -e $output > ~/attempts.json
cat /etc/hosts | grep vm > ~/hosts
"""

def collect_terasort_stats(vms):
    parallel(lambda vm: vm.script(COLLECT_TERASORT_SCRIPT), vms)
    parallel(lambda vm: vm.recv('~/attempts.json', 'vm-' + vm.name + '.json'), vms)
    parallel(lambda vm: vm.recv('~/hosts', 'vm-hosts'), vms)

def argos_start(vms):
    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

def argos_finish(vms):
    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)

    # Delete empty files
    parallel(lambda vm: vm.script('find ~/argos/proc -type f -empty -delete'), vms)
    # Delete empty directories
    parallel(lambda vm: vm.script('find ~/argos/proc -type d -empty -delete'), vms)

    # Save argos results
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)

    # Save argos output
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)


def terasort_with_argos_run(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('ntp'), vms)
    parallel(lambda vm: vm.install('argos'), vms)
    parallel(lambda vm: vm.install('jq'), vms)

    cluster = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk') != 'False')
    cluster.setup()
    cluster.reset()

    output = cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar teragen -Dmapred.map.tasks={1} {2} {0}"'.format(TERASORT_INPUT, env.param('terasort:mappers'), env.param('terasort:rows')))
    teragen_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()

    argos_start(vms)

    cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar terasort -Dmapred.reduce.tasks={2} {0} {1} >output.log 2>&1"'.format(TERASORT_INPUT, TERASORT_OUTPUT, env.param('terasort:reducers')))

    argos_finish(vms)

    collect_terasort_stats(vms)

    terasort_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()
    terasort_out = cluster.master.script('sudo su - hduser -c "cat output.log"').strip()

    file_name = str(time.time()) + '-' + cluster.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write(str(teragen_time) + "," + str(terasort_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(terasort_out)

def terasort_no_argos_run(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('ntp'), vms)

    cluster = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk'))
    cluster.setup()
    cluster.reset()

    output = cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar teragen -Dmapred.map.tasks={1} {2} {0}"'.format(TERASORT_INPUT, env.param('terasort:mappers'), env.param('terasort:rows')))
    teragen_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()

    time.sleep(2)
    cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar terasort -Dmapred.reduce.tasks={2} {0} {1} >output.log 2>&1"'.format(TERASORT_INPUT, TERASORT_OUTPUT, env.param('terasort:reducers')))

    terasort_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()
    terasort_out = cluster.master.script('sudo su - hduser -c "cat output.log"').strip()

    file_name = str(time.time()) + '-' + cluster.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write(str(teragen_time) + "," + str(terasort_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(terasort_out)

def hive_test(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('hive'), vms)
    parallel(lambda vm: vm.install('mahout'), vms)
    parallel(lambda vm: vm.install('bigbench'), vms)

    vms[0].install('bigbench')

    hadoop = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk'))
    hadoop.setup()
    hadoop.reset()

    hive = HiveCluster(hadoop)
    hive.setup()

terasort_run = terasort_with_argos_run

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, terasort_run)
    env.benchmark.executor.run()
