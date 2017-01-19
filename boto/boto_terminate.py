from __future__ import print_function

import boto3

def boto_term():
	
	inst_name = raw_input("Enter instance name to terminate: ")
	print('Attempting to terminate {}'.format(inst_name))

	ec2 = boto3.resource('ec2')

	filt =[{'Name':'tag:Name','Values': [inst_name]}]
	ec2.instances.filter(Filters=filt).terminate()

	print('Done')

if __name__ == "__main__":
		boto_term()
