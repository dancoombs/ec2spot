from __future__ import print_function

import boto3
import base64
import time
import paramiko
import socket

public_ip_address = '35.167.226.22'
send_script = False

# Connect via ssh
print('Connecting via ssh...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# keep trying, might take a minute to set up ssh on server
for i in range(1, 10):
	try:
		ssh.connect(public_ip_address,
		    username='ubuntu',
		    key_filename='/root/.ssh/aws-key.pem')
		print('Connected to {}'.format(public_ip_address))
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
print('ssh -i ~/.ssh/aws-key.pem ubuntu@{}'.format(public_ip_address))