from __future__ import print_function

import boto3
import base64
import time
import paramiko

user_data = """#cloud-config

runcmd:
- mkdir /home/ubuntu/test
- touch /home/ubuntu/test/test.txt

"""

user_data = base64.b64encode(user_data)

client = boto3.client('ec2')
ec2 = boto3.resource('ec2')

bid = raw_input("Enter bid price: ")

resp = client.request_spot_instances(
	SpotPrice=bid,
	InstanceCount=1,
	AvailabilityZoneGroup='us-west-2b',
	Type='one-time',
	LaunchSpecification={
		'ImageId': 'ami-6ab70b0a',
		'KeyName': 'aws-key',
		'InstanceType': 'p2.xlarge',
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
    			'SubnetId': 'subnet-2ac93d63',
    			'Groups': [ 'sg-70ce6b08' ],
    			"AssociatePublicIpAddress": True
			}
		],
	}),

waiter = client.get_waiter('spot_instance_request_fulfilled')
request = resp[0]['SpotInstanceRequests'][0]
requestId = request['SpotInstanceRequestId']
print('Waiting for spot reqeust fulfill...')
waiter.wait(
    SpotInstanceRequestIds=[
        requestId
    ]
)
ids = client.describe_spot_instance_requests(        
    SpotInstanceRequestIds=[
        requestId
    ])
instanceId = ids['SpotInstanceRequests'][0]['InstanceId']
print('Waiting for instance running...')
instance = ec2.Instance(instanceId)
instance.wait_until_running()
print('InstanceId: {}, State: {}, IpAddress: {}'.format(instance.id, instance.state, instance.public_ip_address))

volume_id = 'vol-0236eb89c50b10afd'
print('Attaching {}'.format(volume_id))
resp = client.attach_volume(
		Device='/dev/sdf',
		InstanceId=instanceId,
		VolumeId=volume_id
	)
print('Waiting 30 seconds for volume attach and ssh boot...')
time.sleep(30)

print('Connecting via ssh...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
	ssh.connect(instance.public_ip_address,
	    username='ubuntu',
	    key_filename='/root/.ssh/aws-key.pem')
	print('Connected to {}'.format(instance.public_ip_address))
	return True
except SSHException:
	print('Exception: {}'.format(e))
	print('Waiting 10 seconds before next attempt...')

# print('Sending mount file')
# sftp = ssh.open_sftp()
# sftp.put('mount.sh', '/home/ubuntu/scripts/mount.sh')
# sftp.close()

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