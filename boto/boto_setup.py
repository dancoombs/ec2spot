setup_name = "fast-ai"
cidr = "0.0.0.0/0"
cidr_block = "10.0.0.0/28"

import boto3
from sys import exit, stdout

# keep track of what to tear down if we fail at a stage
setup_status = {
	'assocId': False,
	'allocateAddr': False,
	'instance': False,
	'sg': False,
	'rtAssoc': False,
	'routeTable': False,
	'ig_attach': False,
	'ig' : False,
	'subnet': False,
	'vpc' : False,
}

def cust_print(msg):
	print msg
	stdout.flush()
	write_status('setup_output.txt',setup_status)

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

def write_status(filename, status):
	f = open(filename, 'w+')

	for i in status:
		if status[i]:
			f.write(i+': '+status[i]+'\n')

	f.close()

def clean_and_quit(client):
	if setup_status['assocId']:
		client.disassociate_address(AssociationId=setup_status['assocId'])
	if setup_status['allocateAddr']:
		client.release_address(AllocationId=setup_status['allocAddr'])
	if setup_status['instance']:
		client.terminate_instances(InstanceIds=[setup_status['instance']])
		waiter = client.get_waiter('instance_terminated')
		waiter.wait(InstanceIds=[setup_status['instance']])
	if setup_status['sg']:
		client.delete_security_group(SecurityGroupId=setup_status['sg'])
	if setup_status['rtAssoc']:
		client.disassociate_route_table(AssociationId=setup_status['rtAssoc'])
	if setup_status['routeTable']:
		client.delete_route_table(RouteTableId=setup_status['routeTable'])
	if setup_status['ig_attach']:
		client.detach_internet_gateway(InternetGatewayId=setup_status['ig'],VpcId=setup_status['vpc'])
	if setup_status['ig']:
		client.delete_internet_gateway(InternetGatewayId=setup_status['ig'])
	if setup_status['subnet']:
		client.delete_subnet(SubnetId=setup_status['subnet'])
	if setup_status['vpc']:
		client.delete_vpc(VpcId=setup_status['vpc'])
	quit()

sess = boto3.session.Session()
region = sess.region_name

ami = ''

if region == 'us-west-2':
	ami='ami-bc508adc'
elif region == 'us-east-1':
	ami='ami-31ecfb26'
elif region == 'eu-west-1':
	ami='ami-b43d1ec7'
else:
	cust_print('Only us-[east-1|west-2] and eu-west-1 are currently supported.')
	quit()

ec2 = boto3.resource('ec2')
client = ec2.meta.client

vpc = client.create_vpc(CidrBlock=cidr_block)
try:
	vpcId = vpc['Vpc']['VpcId']
	setup_status['vpc'] = vpcId
	cust_print('vpc '+vpcId+' created...')
except KeyError:
	cust_print('failed to create vpc.')
	clean_and_quit(client)

client.modify_vpc_attribute(VpcId=vpcId,EnableDnsSupport={'Value':True})
client.modify_vpc_attribute(VpcId=vpcId,EnableDnsHostnames={'Value':True})

ig = client.create_internet_gateway()
try:
	igId = ig['InternetGateway']['InternetGatewayId']
	setup_status['ig'] = igId
	cust_print('internet gateway '+igId+' created...')
except KeyError:
	cust_print('failed to create gateway.')
	clean_and_quit(client)

client.attach_internet_gateway(InternetGatewayId=igId,VpcId=vpcId)
setup_status['ig_attach'] = 'true'

subnet = client.create_subnet(VpcId=vpcId,CidrBlock=cidr_block)
try:
	subnetId = subnet['Subnet']['SubnetId']
	setup_status['subnet'] = subnetId
	cust_print('subnet '+subnetId+' created...')
except KeyError:
	cust_print('failed to create subnet.')
	clean_and_quit(client)

rt = client.create_route_table(VpcId=vpcId)
try:
	rtId = rt['RouteTable']['RouteTableId']
	setup_status['routeTable'] = rtId
	cust_print('route table '+rtId+' created...')
except KeyError:
	cust_print('failed to create route table.')
	clean_and_quit(client)

rtAssoc = client.associate_route_table(RouteTableId=rtId,SubnetId=subnetId)
try:
	rtAssoc = rtAssoc['AssociationId']
	setup_status['rtAssoc'] = rtAssoc
	cust_print('association '+rtAssoc+' completed...')
except KeyError:
	cust_print('failed to associate route table.')
	clean_and_quit(client)

client.create_route(RouteTableId=rtId,DestinationCidrBlock=cidr,GatewayId=igId)

sg = client.create_security_group(GroupName=setup_name+'-sg',Description='SG for fast.ai machine',VpcId=vpcId)
try:
	sgId = sg['GroupId']
	setup_status['sg'] = sgId
	cust_print('sg  '+sgId+' created...')
except KeyError:
	cust_print('failed to create sg.')
	clean_and_quit(client)

client.authorize_security_group_ingress(
		GroupId=sgId,
		IpProtocol='tcp',
		FromPort=22,
		ToPort=22,
		CidrIp=cidr
	)
client.authorize_security_group_ingress(GroupId=sgId,IpProtocol='tcp',FromPort=8888,ToPort=8898,CidrIp=cidr)

###########################################################
#todo: check for key pair if it hasn't already been created
###########################################################

instance = client.run_instances(
		ImageId=ami,
		MinCount=1,
		MaxCount=1,
		InstanceType='p2.xlarge',
		KeyName='aws-key-'+setup_name, #this assumes that the key pair has already been setup
		SecurityGroupIds=[sgId],
		SubnetId=subnetId,
		BlockDeviceMappings=[
			{
				'DeviceName':'/dev/sda1',
				'Ebs': {
					'VolumeSize': 128,
					'VolumeType': 'gp2',
				}
			},
		]
	)
try:
	instanceId = instance['Instances'][0]['InstanceId']
	setup_status['instance'] = instanceId
	cust_print('instance '+instanceId+' created...')
except KeyError:
	cust_print('failed to create instance.')
	clean_and_quit(client)

allocAddr = client.allocate_address(Domain='vpc')['AllocationId']
setup_status['allocAddr'] = allocAddr
cust_print('allocation '+allocAddr+' completed...')

waiter = client.get_waiter('instance_running')
cust_print('Waiting for instance to start')
waiter.wait(InstanceIds=[instanceId])

assocId = client.associate_address(InstanceId=instanceId,AllocationId=allocAddr)['AssociationId']
setup_status['assocId'] = assocId
cust_print('instance started, allocation associated')

instances = client.describe_instances(InstanceIds=[instanceId])
try:
	instanceUrl = instances['Reservations'][0]['Instances'][0]['PublicDnsName']
except KeyError:
	cust_print('instance url not found.')
	clean_and_quit(client)

client.reboot_instances(InstanceIds=[instanceId])

cust_print('# connect to the instance')
cust_print('ssh -i ~/.ssh/aws-key-'+setup_name+'.pem ubuntu@'+instanceUrl)

client.create_tags(
		Resources=[
			vpcId,
			igId,
			subnetId,
			rtId,
			instanceId,
		],
		Tags=[
			{
				'Key':'Name', 
				'Value':setup_name
			},
			{
				'Key':'Name', 
				'Value':setup_name+'-gateway'
			},
			{
				'Key':'Name', 
				'Value':setup_name+'-subnet'
			},
			{
				'Key':'Name', 
				'Value':setup_name+'-route-table'
			},
			{
				'Key':'Name', 
				'Value':setup_name+'-gpu-machine'
			},
		],
	)

write_status('setup_output.txt', setup_status)
cust_print('teardown files written to \'setup_output.txt\'.')
