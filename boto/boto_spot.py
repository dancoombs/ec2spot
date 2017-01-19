from __future__ import print_function

import boto3
import base64
import time
import paramiko
import sys
import socket

user_data = """#cloud-config

runcmd:

"""
user_data = base64.b64encode(user_data)

client = boto3.client('ec2')
ec2 = boto3.resource('ec2')

def parse_conf(filename):
	# configuration dictionary
	configs = {}
	
	# open config file
	f = open(filename, 'r')
	data = f.readlines()
	
	# read config file
	for line in data:
		key, value = line.split(": ")
		configs[key.strip()] = value.strip()
	
	f.close()

	return configs

def boto_start(filename, send_script=False):
	bid = raw_input("Enter bid price: ")
	inst_name = raw_input("Enter instance name: ")

	configs = parse_conf(filename)

	# request spot instance with configs
	resp = client.request_spot_instances(
		SpotPrice=bid,
		InstanceCount=1,
		AvailabilityZoneGroup='us-west-2b',
		Type='one-time',
		LaunchSpecification={
			'ImageId': configs['ami_id'],
			'KeyName': configs['ssh_key'],
			'InstanceType': configs['instance_type'],
			'UserData': user_data,
			'BlockDeviceMappings': [
				{
					'DeviceName': '/dev/sda1',
					'Ebs': {
						'VolumeSize': 32,
						'VolumeType': 'gp2',
						'DeleteOnTermination': True
					}
				}
			],
			'NetworkInterfaces': [
				{
				    'DeviceIndex': 0,
	    			'SubnetId': configs['subnet_id'],
	    			'Groups': [ 'sg-70ce6b08' ],
	    			"AssociatePublicIpAddress": True
				}
			]
		})

	# wait for request
	waiter = client.get_waiter('spot_instance_request_fulfilled')
	request = resp['SpotInstanceRequests'][0]
	requestId = request['SpotInstanceRequestId']
	print('Waiting for spot reqeust fulfill...')
	waiter.wait(
	    SpotInstanceRequestIds=[
	        requestId
	    ]
	)

	# get request id
	ids = client.describe_spot_instance_requests(        
	    SpotInstanceRequestIds=[
	        requestId
	    ])

	# get instance id
	instanceId = ids['SpotInstanceRequests'][0]['InstanceId']

	# wait for instance running
	print('Waiting for instance running...')
	instance = ec2.Instance(instanceId)
	instance.wait_until_running()

	# get instance state
	print('InstanceId: {}, State: {}, IpAddress: {}'.format(instance.id, instance.state, instance.public_ip_address))

	# Tag with given name
	instance.create_tags(
			Tags=[{
				'Key': 'Name',
				'Value': inst_name
			},
			]
		)

	# attach volume from configs
	print('Attaching {}'.format(configs['ebs_vol_id']))
	resp = client.attach_volume(
			Device='/dev/sdf',
			InstanceId=instanceId,
			VolumeId=configs['ebs_vol_id']
		)

	# Wait
	print('Waiting 30 seconds for volume attach and ssh boot...')
	time.sleep(30)

	# Connect via ssh
	print('Connecting via ssh...')
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	# keep trying, might take a minute to set up ssh on server
	for i in range(1, 10):
		try:
			ssh.connect(instance.public_ip_address,
			    username='ubuntu',
			    key_filename='/root/.ssh/aws-key.pem')
			print('Connected to {}'.format(instance.public_ip_address))
			break
		except (paramiko.SSHException, socket.error), e:
			print('Exception: {}'.format(e))
			print('Atempt {}, waiting 10 seconds before next attempt...'.format(i))
			time.sleep(10)

	# send mount script if told to
	if send_script:
		print('Sending mount file')
		sftp = ssh.open_sftp()
		sftp.put('mount.sh', '/home/ubuntu/scripts/mount.sh')
		sftp.close()

	# execute mount script
	print('Executing mount')
	stdin, stdout, stderr = ssh.exec_command('sudo bash /home/ubuntu/scripts/mount.sh')
	stdin.flush()
	data = stdout.read().splitlines()
	print('mount.sh output:')
	for line in data:
	    print(line)
	ssh.close()
	print('Okay to connect!')
	print('ssh -i ~/.ssh/aws-key.pem ubuntu@{}'.format(instance.public_ip_address))


if __name__ == "__main__":
	if len(sys.argv) <  3 | len(sys.argv) > 4:
		print("Usage: python boto_spot <config file> [OPTIONAL] send_script=True/False")
	else:
		if len(sys.argv) == 3:
			_, send_mnt = sys.argv[2].split('=')
			boto_start(sys.argv[1], send_mount=(send_mnt=='True'))
		else:
			boto_start(sys.argv[1])