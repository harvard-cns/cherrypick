import base64
import shlex
import subprocess
import time
from threading import RLock

from cloudbench import constants
from cloudbench.util import Debug
from cloudbench.env.entity.model import Location

from .base import Cloud


AWS_STATE_PENDING=0
AWS_STATE_RUNNING=16


class AwsCloud(Cloud):
    def __init__(self, *args, **kwargs):
        super(AwsCloud, self).__init__(*args, **kwargs)
        self.lock = RLock()
        constants.DEFAULT_VM_USERNAME = 'ubuntu'
        self.security_groups = {}

    def execute(self, cmd, output={}):
        repeat = True
        ret = True

        while True:
            ret = super(AwsCloud, self).execute(cmd, output)
            if 'NTPException' not in output['stderr']:
                break
            print "Retrying the aws command."

        return ret
                

    def location_of(self, entity):
        if hasattr(entity, 'location'):
            if callable(entity.location) and isinstance(entity.location(), Location):
                return entity.location().location
            return entity.location

    def to_location_of(self, entity):
        def switch_to(location):
            return self.execute(['aws', 'configure', 'set', 'region', location])
        switch_to(self.location_of(entity))
        return True

    def vm_name(self, vm):
        """ Return the name of the VM, to avoid conflicts with the other entities """
        return 'vm-' + vm.name

    def vm_id(self, vm, throw=False):
        """ Return the ID of the VM """
        return self.get_id(vm, 'vm', throw)

    def sg_name(self, sg, location):
        """ Return the name of the security-group, to avoid conflicts with the other entities """
        return 'sg-' + sg.name + '-' + location

    def sg_id(self, sg, location, throw=False):
        """ Return the ID of the Security group"""
        vid = self.data[self.sg_name(sg, location)]
        if throw and (not vid):
            raise KeyError("No such %s exists" % entity.__class__.__name__)
        return vid

    def get_id(self, entity, prefix, throw=False):
        vid = self.data[getattr(self, prefix+'_name')(entity)]
        if throw and (not vid):
            raise KeyError("No such %s exists" % entity.__class__.__name__)
        return vid

    def exe(self, cmd, output={}):
        """ Short hand for running aws commands """
        cmd = 'aws ec2 ' + cmd
        return self.execute(shlex.split(cmd), output)

    def vid(self, vm):
        "Vpcs[?State=='available'].VpcId | [0]"

    def start_virtual_machine(self, vm):
        # aws ec2 start-instances --instance-ids <the instance id you get from the output of run-instances>
        with self.lock:
            print "Starting the Virtual Machine: %s" % vm
            self.to_location_of(vm)
            vid = self.vm_id(vm, throw=True)
            cmd = ['aws', 'ec2', 'start-instances',
                    '--instance-ids', self.data[self.vm_name(vm)]]
            output = {}
            return self.execute(cmd, output)

    def stop_virtual_machine(self, vm):
        # aws ec2 stop-instances --instance-ids <the instance id you get from the output of run-instances>
        with self.lock:
            print "Stopping the Virtual Machine: %s" % vm
            if self.vm_id(vm, throw=True) is None:
                return True

            self.to_location_of(vm)
            vid = self.vm_id(vm, throw=True)
            cmd = ['aws', 'ec2', 'stop-instances',
                    '--instance-ids', self.data[self.vm_name(vm)]]
            
            output = {}
            return self.execute(cmd, output)

    def address_virtual_machine(self, vm):
        # the hostname of AWS VMs are not directly from the name you gave it.
        # check the name from "aws ec3 describe-instances"
        output = {}
        while True:
            with self.lock:
                print "Returning Virtual Machine Address."
                self.to_location_of(vm)
                vid = self.vm_id(vm, throw=True)
                cmd = ['aws', 'ec2', 'describe-instances', '--instance-ids',
                        vid, '--query', '"Reservations[0].Instances[0].PublicIpAddress"']
                self.execute(cmd, output)

            if output['stdout'].strip():
                return output['stdout'].strip().replace('"', '')

            time.sleep(5)

    def random_name(self):
        import uuid
        return 'rand-' + str(uuid.uuid4()).split('-')[0]

    def sg_for_loc(self, location):
        location = self.location_of(location)
        if self.data['security-group-' + location] is not None:
            return self.data['security-group-' + location]

        name = self.random_name()
        self.data['security-group-' + location] = name
        return name

    def create_location(self, group):
        # You should have a VPC for each location.

        # step 1st: you should explicit switch to the target location with "aws configure set location <location name>".

        # step 2nd: read the current VPC in the location with "aws ec2 describe-vpcs".
        # or create a new VPC with "aws ec2 create-vpc"

        # Note: read the output and remember the id of VPC
        with self.lock:
            print 'Initiating location (%s)' % group
            self.to_location_of(group)

            #TODO: Try to create the security group
            cmd = ['aws', 'ec2', 'create-security-group', '--group-name',
                    self.sg_for_loc(group), '--description', '"Benchmark group"']
            self.execute(cmd)

            cmd = ['aws', 'ec2', 'authorize-security-group-ingress',
                   '--group-name', self.sg_for_loc(group), '--protocol',
                   'tcp', '--port', '22', '--cidr', '0.0.0.0/0']
            self.execute(cmd)

            return True


    def setup_security_group(self, ep, location):
        if not self.sg_id(ep, location):
            # Create the security-group
            cmd = ['aws', 'ec2', 'create-security-group', '--group-name',
                    ep.name, '--description', '"Benchmark group"',
                    '--query', 'GroupId']
            self.execute(cmd)

            cmd = ['aws', 'ec2', 'describe-security-groups',
                    '--filters', 'Name=group-name,Values=' + ep.name,
                    '--query', 'SecurityGroups[0].GroupId']
            output = {}
            self.execute(cmd, output)
            self.data[self.sg_name(ep, location)] = output['stdout'].strip().replace('"', '')

            # Enable SSH
            cmd = ['aws', 'ec2', 'authorize-security-group-ingress',
                   '--group-name', ep.name, '--protocol',
                   'tcp', '--port', '22', '--cidr', '0.0.0.0/0']
            self.execute(cmd)

            # Enable security-group port
            cmd = ['aws', 'ec2', 'authorize-security-group-ingress',
                    '--group-name', ep.name, '--protocol', ep.protocol,
                    '--port', ep.public_port, '--cidr', '0.0.0.0/0']
            self.execute(cmd)


    def create_security_group(self, ep):
        # you can manually create a security group on web portal and always use the security group id when you create VMs.
        with self.lock:

            for vm in ep.virtual_machines():
                self.to_location_of(vm)

                sg_ids = []
                for sg in vm.security_groups():
                    self.setup_security_group(sg, self.location_of(vm))
                    sg_ids.append(self.sg_id(sg, self.location_of(vm)))

                cmd = ['aws', 'ec2', 'modify-instance-attribute',
                       '--groups', ','.join(sg_ids), '--instance-id',
                       self.vm_id(vm)]
                self.execute(cmd)

            return True

    def create_virtual_machine(self, vm):
        
        # aws ec2 run-instances --image-id ami-5189a661 --count 1 --instance-type t2.micro --key-name CloudBench --subnet-id subnet-155fe170
        
        # Note: you need to parse the output for the real VM id and remember it.

        # Note: different datacenters (locations) have different image-id even for the same OS type and version. Refer data/awsaims.txt for the mapping from locations to image-id.
        with self.lock:
            print 'Creating virtual machine (%s)' % vm
            self.to_location_of(vm)
            output = {}

            ret = self.exe('run-instances --image-id {0} --count 1 \
            --instance-type {1} --key-name=cloud --security-groups {2} \
            --query "Instances[0].InstanceId"'.format(
                vm.image, vm.type, self.sg_for_loc(vm)),
                output)
            if ret:
                    self.data[self.vm_name(vm)] = output['stdout'].strip()
            return ret

    def vnet_name(self, vnet):
        """ Return the name of the VNet to avoid conflicts """
        return 'net-' + vnet.name

    def subnet_name(self, vnet):
        return self.vnet_name(vnet) + '-subnet'

    def vnet_id(self, vnet, throw=False):
        """ Return the ID of the VM """
        return self.get_id(vnet, 'vnet', throw)

    def status_virtual_machine(self, vm):
        with self.lock:
            print "Returning the status of the virtual-machine"
            if self.vm_id(vm) is None:
                return True

            self.to_location_of(vm)
            output = {}
            self.exe('describe-instances --instance-ids {0} --query \
            "Reservations[0].Instances[0].State.Code"'.format(self.vm_id(vm)), output)

            print output
            if (not (output['stdout'].strip())):
                return None

            if (int(output['stdout'].strip().replace('"', '')) == AWS_STATE_RUNNING):
                return True

            if (int(output['stdout'].strip().replace('"', '')) == AWS_STATE_PENDING):
                return None

            return False

    def create_virtual_network(self, vnet):
        print 'Creating virtual network (%s)' % vnet
        # aws ec2 create-subnet --vpc-id <value> --cidr-block <IP prefix with "/">.

        with self.lock:
            self.to_location_of(vnet)
            output = {}
            if self.vnet_id(vnet) is None:
                return True

            cidr_block = vnet.address_range
            if not self.exe('create-vpc --cidr-block {0} --query "Vpc.VpcId"'.format(cidr_block), output):
                raise Exception("Error creating the virtual network")
            self.data[self.vnet_name(vnet)] = output['stdout'].strip()

            # Get the VNet ID
            vid = self.vnet_id(vnet, throw=True)

            # Create a subnet equal to the VNet size
            if not self.exe('create-subnet --vpc-id {0} --cidr-block {1} \
                    --query "Subnet.SubnetId"'.format(vid,
                        vnet.address_range), output):
                raise Exception("Failed to create the subnet")
            self.data[self.subnet_name(vnet) + '-subnet'] = output['stdout'].strip()
            return True

    def delete_security_group(self, group):
        print "Deleting security group (%s)" % group
        with self.lock:
            for vm in group.virtual_machines():
                loc = self.location_of(vm)
                if not self.data[self.sg_name(group, loc)]:
                    continue

                self.to_location_of(vm)
                cmd = ['aws', 'ec2', 'delete-security-group', '--group-name',
                        group.name]
                self.execute(cmd)
                del self.data[self.sg_name(group, loc)]
        # aws ec2 delete-security-group
        return True

    def delete_virtual_machine(self, vm):
        with self.lock:
            print "Deleting virtual machine (%s)" % vm
            # Return true if we have already deleted this one
            if not self.vm_id(vm, throw=False):
                return True

            self.to_location_of(vm)
            output = {}
            ret = self.exe('terminate-instances --instance-ids \
                    {0}'.format(self.vm_id(vm, throw=True)), output)

            if ret:
                del self.data['vm-' + vm.name]

            return ret

    def delete_virtual_network(self, vnet):
        # aws ec2 delete-subnet
        # Return true if we have already deleted this vnet
        with self.lock:
            print "Deleting virtual network (%s)" % vnet
            if not self.vnet_id(vnet, throw=False):
                return True

            self.to_location_of(vnet)
            ret = self.exe('aws ec2 delete-vpc --vpc-id {0}'.format(self.vnet_id(vnet, throw=True)))
            if ret:
                del self.data[self.vnet_name(vnet)]
                del self.data[self.subnet_name(vnet)]
            return ret

    def delete_location(self, group):
        # aws ec2 delete-security-group
        print "Deleting location (%s)" % group

        with self.lock:
            if not self.data['security-group-' + group.location]:
                return True
            
            self.to_location_of(group)
            ret = self.exe('delete-security-group --group-name {0}'.format(self.sg_for_loc(group)))
            if ret:
                del self.data['security-group-' + group.location]

            return True
