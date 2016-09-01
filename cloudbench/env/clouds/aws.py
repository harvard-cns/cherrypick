import base64
import json
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
        self.addresses = {}

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
        print cmd
        cmd = 'echo ' + base64.b64encode('aws ec2 ' + cmd) + ' | base64 -d | bash'
        return self.execute(shlex.split(cmd), output)

    def vid(self, vm):
        return "Vpcs[?State=='available'].VpcId | [0]"

    def gw_name(self, vnet):
        return 'gw-' + vnet.name

    def gw_id(self, vnet, throw=False):
        return self.get_id(vnet, 'gw', throw)

    def start_virtual_machine(self, vm):
        # aws ec2 start-instances --instance-ids <the instance id you get from the output of run-instances>
        with self.lock:
            self.to_location_of(vm)
            vid = self.vm_id(vm, throw=True)
            cmd = ['aws', 'ec2', 'start-instances',
                    '--instance-ids', self.data[self.vm_name(vm)]]
            output = {}
            return self.execute(cmd, output)

    def stop_virtual_machine(self, vm):
        # aws ec2 stop-instances --instance-ids <the instance id you get from the output of run-instances>
        with self.lock:
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
        print self.addresses
        if vm.name in self.addresses:
            return self.addresses[vm.name]

        while True:
            with self.lock:
                self.to_location_of(vm)
                vid = self.vm_id(vm, throw=True)
                cmd = ['aws', 'ec2', 'describe-instances', '--instance-ids',
                        vid, '--query', '"Reservations[0].Instances[0].PublicIpAddress"']
                self.execute(cmd, output)

            if output['stdout'].strip():
                ip = output['stdout'].strip().replace('"', '')
                self.addresses[vm.name] = ip
                return ip

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
        return True
        # you can manually create a security group on web portal and always use the security group id when you create VMs.
        with self.lock:

            for vm in ep.virtual_machines():
                self.to_location_of(vm)

                sg_ids = []
                for sg in vm.security_groups():
                    self.setup_security_group(sg, self.location_of(vm))
                    sg_ids.append(self.sg_id(sg, self.location_of(vm)))

                # cmd = ['aws', 'ec2', 'modify-instance-attribute',
                #        '--groups', ' '.join(sg_ids), '--instance-id',
                #        self.vm_id(vm)]
                # self.execute(cmd)

            return True

    def availability_zone_of_subnet(self, subnet_id):
        output = {}
        self.exe('describe-subnets --filter Name=subnet-id,Values=%s --query=Subnets[0].AvailabilityZone' % subnet_id, output)
        return output['stdout'].strip().replace('"', '')

    def create_virtual_machine(self, vm):
        
        # aws ec2 run-instances --image-id ami-5189a661 --count 1 --instance-type t2.micro --key-name CloudBench --subnet-id subnet-155fe170
        
        # Note: you need to parse the output for the real VM id and remember it.

        # Note: different datacenters (locations) have different image-id even for the same OS type and version. Refer data/awsaims.txt for the mapping from locations to image-id.
        with self.lock:
            self.to_location_of(vm)
            output = {}


            net_cmd = '--security-groups {0}'.format(self.sg_for_loc(vm))
            if vm.virtual_network():
                vm_az = self.default_availability_zone(vm.virtual_network())
                try:
                    if vm.availability_zone is not None:
                        vm_az = vm.availability_zone
                except Exception:
                    pass

                subnet_id = self.find_or_create_subnet(vm.virtual_network(), vm_az)
                net_cmd = '--subnet-id=%s' % subnet_id
                if 'placement_group' in vm.virtual_network() and (vm.virtual_network().placement_group == "true"):
                    net_cmd = net_cmd + ' --placement AvailabilityZone=%s,GroupName=%s,Tenancy=default' % (self.availability_zone_of_subnet(subnet_id), self.pg_name(vm.virtual_network()))

            storage_cmd = ''
            try:
                if vm.storage is None:
                    raise "No storage specified."
                    
                storage_specs = []

                # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html
                storage_paths = map(lambda x: '/dev/sd' + x, list('fghijklmnop'))
                storage_spec = '{\\"DeviceName\\": \\"%s\\",\\"Ebs\\":{\\"VolumeSize\\":%d, \\"VolumeType\\": \\"%s\\"}}'

                for i in range(vm.storage_count):
                    storage_specs.append(storage_spec % (storage_paths[i], vm.storage_size, vm.storage_type))

                storage_cmd = \
                    '--block-device-mappings "[%s]"' % ','.join(storage_specs)
            except Exception:
                pass

            extra_cmd = []

            def ephemeral_storage_mapping(count=1):
                storage_spec = '{\\"DeviceName\\": \\"%s\\",\\"VirtualName\\": \\"%s\\"}'
                disks = map(chr, range(ord('b'),ord('b')+count))

                storage_disks = []

                eph_disk = 0
                for disk in disks:
                    storage_disks.append(storage_spec % ('/dev/sd' + disk, "ephemeral" + str(eph_disk)))
                    eph_disk += 1

                storage_cmd = '--block-device-mappings "[%s]"' % ','.join(storage_disks)
                return storage_cmd


            # Instances that are not automatically ebs optimized but can be made to do so
            can_ebs_optimized_instances = [
                    "c1.xlarge" , "c3.xlarge" , "c3.2xlarge", "c3.4xlarge",
                    "g2.2xlarge", "i2.xlarge" , "i2.2xlarge", "i2.4xlarge",
                    "m1.large"  , "m1.xlarge" , "m2.2xlarge", "m2.4xlarge",
                    "m3.xlarge" , "m3.2xlarge", "r3.xlarge" , "r3.2xlarge",
                    "r3.4xlarge"]

            can_ephemeral_instances = {
                    'i2.xlarge' : 1,
                    'i2.2xlarge': 2,
                    'i2.4xlarge': 4,
                    'i2.8xlarge': 8}

            if vm.type in can_ebs_optimized_instances:
                extra_cmd.append('--ebs-optimized')

            if vm.type in can_ephemeral_instances:
                extra_cmd.append(
                        ephemeral_storage_mapping(
                            can_ephemeral_instances[vm.type]))

            ret = self.exe('run-instances --image-id %s --count 1 \
                    --instance-type %s --key-name=cloud %s\
                    %s %s --query "Instances[0].InstanceId"' % (vm.image, vm.type, net_cmd, storage_cmd, ' '.join(extra_cmd)), output)

            if ret:
                    self.data[self.vm_name(vm)] = output['stdout'].strip()
            return ret

    def vnet_name(self, vnet):
        """ Return the name of the VNet to avoid conflicts """
        return 'net-' + vnet.name

    def subnet_name(self, vnet, az):
        return self.vnet_name(vnet) + '-' + az + '-subnet'

    def subnet_id(self, vnet, az, throw=False):
        vid = self.data[self.subnet_name(vnet, az)]
        if throw and (not vid):
            raise KeyError("No such %s exists" % entity.__class__.__name__)
        return vid

    def pg_name(self, vnet):
        """ Return the name of the placement group for our Virtual Network """
        return self.unique('pg-' + vnet.name)

    def vnet_id(self, vnet, throw=False):
        """ Return the ID of the VM """
        return self.get_id(vnet, 'vnet', throw)

    def status_virtual_machine(self, vm):
        with self.lock:
            if self.vm_id(vm) is None:
                return True

            self.to_location_of(vm)
            output = {}
            self.exe('describe-instances --instance-ids {0} --query \
            "Reservations[0].Instances[0].State.Code"'.format(self.vm_id(vm)), output)

            if (not (output['stdout'].strip())):
                return None

            if (int(output['stdout'].strip().replace('"', '')) == AWS_STATE_RUNNING):
                return True

            if (int(output['stdout'].strip().replace('"', '')) == AWS_STATE_PENDING):
                return None

            return False

    def subnet_range_for_availability_zone(self, vnet, availability_zone):
        parts = vnet.address_range.split(".")
        subnet = str(ord(availability_zone[-1]) - ord('a'))
        return ".".join([parts[0], parts[1], subnet, '0/24'])


    def create_subnet(self, vnet, availability_zone):
        vid = self.vnet_id(vnet, throw=True)
        subnet_range = self.subnet_range_for_availability_zone(vnet, availability_zone)
        output = {}

        # Create a subnet equal to the VNet size
        if not self.exe('create-subnet --vpc-id {0} --cidr-block {1} --availability-zone {2}\
                --query "Subnet.SubnetId"'.format(
                    vid, subnet_range, availability_zone
                ), output):
            raise Exception("Failed to create the subnet")
        subnet_id = output['stdout'].strip()
        self.exe('modify-subnet-attribute --subnet-id=%s --map-public-ip-on-launch' % subnet_id)
        self.data[self.subnet_name(vnet, availability_zone)] = subnet_id
        return subnet_id

    def find_or_create_subnet(self, vnet, availability_zone):
        sid = self.subnet_id(vnet, availability_zone, throw=False)
        if sid is not None:
            return sid
        
        return self.create_subnet(vnet, availability_zone)


    def delete_subnet(self, vnet, availability_zone):
        try:
            ret = self.exe('delete-subnet --subnet-id {0}'.format(self.subnet_id(vnet, availability_zone, throw=False)))
            if ret:
                del self.data[self.subnet_name(vnet, availability_zone)]
        except Exception:
            pass

    def default_availability_zone(self, vnet):
        return self.list_availability_zones(vnet)[0]

    def list_availability_zones(self, vnet):
        with self.lock:
            self.to_location_of(vnet)
            output = {}
            ret = self.exe('describe-availability-zones --region {0} --query "AvailabilityZones[*].ZoneName"'.format(self.location_of(vnet)), output)
            print output
            return json.loads(output['stdout'])

    def create_virtual_network(self, vnet):
        # aws ec2 create-subnet --vpc-id <value> --cidr-block <IP prefix with "/">.
        with self.lock:
            self.to_location_of(vnet)
            output = {}
            if self.vnet_id(vnet) is not None:
                return True

            cidr_block = vnet.address_range
            if not self.exe('create-vpc --cidr-block {0} --query "Vpc.VpcId"'.format(cidr_block), output):
                raise Exception("Error creating the virtual network")
            self.data[self.vnet_name(vnet)] = output['stdout'].strip()

            # Get the VNet ID
            vid = self.vnet_id(vnet, throw=True)

            # Setup the security group rules
            self.exe('describe-security-groups --filter="Name=vpc-id,Values={0}" --query="SecurityGroups[0].GroupId"'.format(vid), output)
            sg_id = output['stdout'].strip().replace('"', '')
            self.exe('authorize-security-group-ingress --protocol=-1 --group-id={0} --cidr=0.0.0.0/0'.format(sg_id))

            # Create an attach an internet gateway
            output = {}
            self.exe('create-internet-gateway --query \'InternetGateway.InternetGatewayId\'', output)
            gw_id = output['stdout'].strip().replace('"', '')
            self.data[self.gw_name(vnet)] = gw_id

            self.exe('attach-internet-gateway --internet-gateway-id {1} --vpc-id {0}'.format(self.vnet_id(vnet), gw_id))

            # Setup the default route to the gateway
            self.exe('describe-route-tables --filter "Name=vpc-id,Values={0}" --query \'RouteTables[0].RouteTableId\''.format(self.vnet_id(vnet)),output) 
            rtb_id = output['stdout'].strip().replace('"', '')
            self.exe('create-route --route-table-id {0} --destination-cidr-block 0.0.0.0/0 --gateway-id {1}'.format(rtb_id, gw_id))


            # Setup the placement group if one is asked
            if 'placement_group' in vnet and (vnet.placement_group == "true"):
                self.exe('create-placement-group --group-name %s --strategy cluster' % self.pg_name(vnet), output)
            return True

    def delete_security_group(self, group):
        return True
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

    def delete_subnets(self, vnet):
        with self.lock:
            self.to_location_of(vnet)
            for az in self.list_availability_zones(vnet):
                self.delete_subnet(vnet, az)

    def delete_virtual_network(self, vnet):
        # aws ec2 delete-subnet
        # Return true if we have already deleted this vnet
        with self.lock:
            if not self.vnet_id(vnet, throw=False):
                return True

            self.to_location_of(vnet)
            if 'placement_group' in vnet and (vnet.placement_group == "true"):
                self.exe('delete-placement-group --group-name %s' % self.pg_name(vnet))

            ret = self.exe('detach-internet-gateway --internet-gateway-id {0} --vpc-id {1}'.format(self.gw_id(vnet, throw=False), self.vnet_id(vnet, throw=False)))
            ret = self.exe('delete-internet-gateway --internet-gateway-id {0}'.format(self.gw_id(vnet, throw=False)))
            self.delete_subnets(vnet)
            ret = self.exe('delete-vpc --vpc-id {0}'.format(self.vnet_id(vnet, throw=False)))
            if ret:
                del self.data[self.vnet_name(vnet)]
                del self.data[self.gw_name(vnet)]
            return True

    def delete_location(self, group):
        # aws ec2 delete-security-group

        with self.lock:
            if not self.data['security-group-' + group.location]:
                return True
            
            self.to_location_of(group)
            ret = self.exe('delete-security-group --group-name {0}'.format(self.sg_for_loc(group)))
            if ret:
                del self.data['security-group-' + group.location]

            return True
