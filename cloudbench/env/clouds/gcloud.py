import base64
import shlex
import subprocess
import time

from cloudbench import constants
from cloudbench.util import Debug, parallel, rate_limit

from .base import Cloud

GCLOUD_STATUS_STOPPED='TERMINATED'
GCLOUD_STATUS_STARTED='RUNNING'

class GcloudCloud(Cloud):
    def project_id(self):
        return constants.DEFAULT_GCLOUD_PROJECT_ID

    def __init__(self, *args, **kwargs):
        super(GcloudCloud, self).__init__(*args, **kwargs)

    def exe(self, cmd, output={}):
        """ Short hand for running aws commands """
        cmd = 'gcloud compute ' + cmd
        ret = self.execute(shlex.split(cmd), output)

        if ('not found' in output['stderr']):
            return True

        return ret

    def virtual_networks_of_security_group(self, sg):
        vnets = set()
        for vm in sg.virtual_machines():
            if vm.virtual_network():
                vnets.add(self.unique(vm.virtual_network().name))
            else:
                vnets.add('default')
        return vnets

    def get_virtual_machine_parameter(self, vm, key):
        output = {}
        ret = self.exe("instances describe {0} --zone {1}".format(
            self.unique(vm.name), vm.location().location), output)

        for line in output['stdout'].split("\n"):
            if line.strip().startswith(key):
                return line.strip().split(": ")[1]

        return None

    def start_virtual_machine(self, vm):
        #gcloud compute instances start omid --zone [LOCATION]
        return self.exe("instances start {0} --zone {1}".format(
            self.unique(vm.name), vm.location().location))

    def stop_virtual_machine(self, vm):
        return self.exe("instances stop {0} --zone {1}".format(
            self.unique(vm.name), vm.location().location))

    def status_virtual_machine(self, vm):
        status = self.get_virtual_machine_parameter(vm, 'status')
        if status == GCLOUD_STATUS_STARTED:
            return True
        elif status == GCLOUD_STATUS_STOPPED:
            return False
        return None

    def exists_virtual_machine(self, vm):
        return True

    def address_virtual_machine(self, vm):
        return self.get_virtual_machine_parameter(vm, 'natIP')

    def create_location(self, group):
        # Do nothing?
        return True

    def create_security_group(self, ep):
        # gcloud compute firewall-rules create internal --network [NAME] --source-ranges [RANGE] --allow [protocols]
        vnets = self.virtual_networks_of_security_group(ep)

        ret = True

        for vnet in vnets:
            ret = ret and self.exe("firewall-rules create {0} --network {1} --allow {2}".format(
                        self.unique(ep.name)+'-'+vnet, vnet,
                        ep.protocol + ':' + ep.public_port))
        return ret

    def create_virtual_machine(self, vm):
        # gcloud compute instances create [NAME] --zone [ZONE/Location] --machine-type [TYPE] --image [IMAGE] --network [NETWORK]
        cmd = "instances create {0} --zone {1} --machine-type {2} --image {3} --metadata-from-file sshKeys={4}".format(
              self.unique(vm.name), vm.location().location, vm.type, vm.image, constants.DEFAULT_GCLOUD_PUBLIC_KEY)

        if vm.virtual_network():
            cmd += ' --network {0}'.format(self.unique(vm.virtual_network().name))

        self.exe(cmd)
        return True

    def create_virtual_network(self, vnet):
        # gcloud compute networks create [NAME] --range [CIDR/IP]
        # gcloud compute firewall-rules create [NAME] --network [NAME] --source-ranges [RANGE] --allow [protocols]
        ret = self.exe(
            "networks create {0} --range {1}".format(
                self.unique(vnet.name), vnet.address_range))
        self.exe("firewall-rules create {0} --network {1} --allow {2}".format(
            'ssh-' + self.unique(vnet.name), self.unique(vnet.name), 'tcp:22'))
        return True



    def delete_security_group(self, ep):
        vnets = self.virtual_networks_of_security_group(ep)

        ret = True
        for vnet in vnets:
            ret = ret and self.exe("firewall-rules delete {0} -q".format(
                        self.unique(ep.name)+'-'+vnet))
        return True

    def delete_virtual_machine(self, vm):
        # gcloud compute instances delete [NAME] --zone [ZONE] -q
        return self.exe("instances delete {0} --zone {1} -q".format(
            self.unique(vm.name), vm.location().location))

    def delete_virtual_network(self, vnet):
        self.exe("firewall-rules delete {0} -q".format('ssh-' + self.unique(vnet.name)))
        return self.exe('networks delete {0} -q'.format(self.unique(vnet.name)))

    def delete_location(self, group):
        # Do nothing?
        return True
