from __future__ import print_function

import boto3

print('Terminating all p2.xlarge instances')
ec2 = boto3.resource('ec2')
ec2.instances.filter(
	Filters=[
		{
		 	'Name':'instance-type',
		 	'Values': ['p2.xlarge']
		}
	]).terminate()
print('Done')