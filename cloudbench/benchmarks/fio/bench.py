def run(env):
    vm1 = env.get('vm1')
    vm2 = env.get('vm2')

    vm1.ssh() << "iperf -s"

    vm2ssh = vm2.ssh()
    vm2ssh << "iperf -c " + vm1.ip
    vm2ssh.wait()

    vm1.terminate()
    vm2.terminate()


