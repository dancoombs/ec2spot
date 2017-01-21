details_file = 'setup_output.txt'

import boto3

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

setup_info = parse_conf(details_file)

steps = len(setup_info)

ec2 = boto3.resource('ec2')
client = ec2.meta.client

if steps > 9: # whole thing completed
	client.disassociate_address(AssociationId=setup_info['assocId'])
	client.disassociate_route_table(AssociationId=setup_info['rtAssoc'])
	client.detach_internet_gateway(InternetGatewayId=setup_info['ig'],VpcId=setup_info['vpc'])
	client.delete_security_group(GroupId=setup_info['sg'])
	client.release_address(AllocationId=setup_info['allocAddr'])	
	client.terminate_instances(InstanceIds=[setup_info['instance']])
	waiter = client.get_waiter('instance_terminated')
	waiter.wait(InstanceIds=[setup_info['instance']])
elif steps > 5:
	client.delete_security_group(GroupId=setup_info['sg'])
	client.disassociate_route_table(AssociationId=setup_info['rtAssoc'])
	client.detach_internet_gateway(InternetGatewayId=setup_info['ig'],VpcId=setup_info['vpc'])
elif steps > 3:
	client.detach_internet_gateway(InternetGatewayId=setup_info['ig'],VpcId=setup_info['vpc'])

try:
	client.delete_route_table(RouteTableId=setup_info['routeTable'])
	client.delete_internet_gateway(InternetGatewayId=setup_info['ig'])
	client.delete_subnet(SubnetId=setup_info['subnet'])
	client.delete_vpc(VpcId=setup_info['vpc'])
except KeyError as err:
	print 'encountered error in final cleanup; '+steps+' steps attempted.'
