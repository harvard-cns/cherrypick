from cloudbench.util import Config
import time


KERNEL4_SCRIPT = """
export DEBIAN_FRONTEND=noninteractive
cd /tmp

wget -rc -nd "http://kernel.ubuntu.com/~kernel-ppa/mainline/v4.1.5-unstable/linux-headers-4.1.5-040105-generic_4.1.5-040105.201508101730_amd64.deb"
wget -rc -nd "http://kernel.ubuntu.com/~kernel-ppa/mainline/v4.1.5-unstable/linux-headers-4.1.5-040105_4.1.5-040105.201508101730_all.deb"
wget -rc -nd "http://kernel.ubuntu.com/~kernel-ppa/mainline/v4.1.5-unstable/linux-image-4.1.5-040105-generic_4.1.5-040105.201508101730_amd64.deb"

aptitude update -y
aptitude install debconf-utils

touch omid.1
echo grub grub/update_grub_changeprompt_threeway select install_new | sudo /usr/bin/debconf-set-selections
echo grub-legacy-ec2 grub/update_grub_changeprompt_threeway select install_new | sudo /usr/bin/debconf-set-selections

sleep 5

touch omid.2
sudo dpkg -i linux-headers*deb linux-image*deb

touch omid.3
cp /usr/src/linux-headers-4.1.5-040105/include/uapi/linux/tcp.h /usr/include/linux/tcp.h

touch omid.4
sed -i 's/_UAPI//g' /usr/include/linux/tcp.h
"""

def install(vm):
    if vm.script('uname -r').startswith('4.1'):
        return

    vm.package_manager.install('build-essential')
    vm.script(KERNEL4_SCRIPT)
    vm.script('reboot')
    time.sleep(60)

def remove(vm):
    print("Use another kernel installation script to rollback")

def installed(vm):
    return vm.script('uname -r').startswith('4.1')
