import subprocess
import base64

from cloudbench import constants
from cloudbench.util import Debug

from .base import Cloud

class AwsCloud(Cloud):
    def start_virtual_machine(self, vm):
        print 'Booting up (%s)' % vm
        # aws ec2 start-instances --instance-ids <the instance id you get from the output of run-instances>
        return True

    def stop_virtual_machine(self, vm):
        print 'Stopping up (%s)' % vm
        # aws ec2 stop-instances --instance-ids <the instance id you get from the output of run-instances>
        return True

    def address_virtual_machine(self, vm):
        # the hostname of AWS VMs are not directly from the name you gave it.
        # check the name from "aws ec2 describe-instances"
        return ""

    def hashify_22(self, name):
        import hashlib
        return str(hashlib.md5(name).hexdigest())[0:22]

    def create_location(self, group):
        print 'Initiating location (%s)' % group
        # You should have a VPC for each location.

        # step 1st: you should explicit switch to the target location with "aws configure set location <location name>".

        # step 2nd: read the current VPC in the location with "aws ec2 describe-vpcs".
        # or create a new VPC with "aws ec2 create-vpc"

        # Note: read the output and remember the id of VPC
        return True

    def create_security_group(self, ep):
        print 'Creating security group (%s)' % ep
        # you can manually create a security group on web portal and always use the security group id when you create VMs.
        return True

    def create_virtual_machine(self, vm):
        print 'Creating virtual machine (%s)' % vm
        # aws ec2 run-instances --image-id ami-5189a661 --count 1 --instance-type t2.micro --key-name CloudBench --subnet-id subnet-155fe170
        
        # Note: you need to parse the output for the real VM id and remember it.

        # Note: different datacenters (locations) have different image-id even for the same OS type and version. Refer data/awsaims.txt for the mapping from locations to image-id.
        return True

    def create_virtual_network(self, vnet):
        print 'Creating virtual network (%s)' % vnet
        # aws ec2 create-subnet --vpc-id <value> --cidr-block <IP prefix with "/">.
        return True

    def delete_security_group(self, group):
        print "Deleting security group (%s)" % group
        # aws ec2 delete-security-group
        return True

    def delete_virtual_machine(self, vm):
        print "Deleting virtual machine (%s)" % vm
        # aws ec2 terminate-instances
        return True

    def delete_virtual_network(self, vnet):
        print "Deleting virtual network (%s)" % vnet
        # aws ec2 delete-subnet
        return True

    def delete_location(self, group):
        print "Deleting location (%s)" % group
        # aws no need to delete a location. maybe you can leave just one VPC per location.
        return True

