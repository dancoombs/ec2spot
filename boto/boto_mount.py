from __future__ import print_function

import boto3
import base64
import time
import paramiko

public_ip_address = '52.11.140.61'

print('Connecting via ssh...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(public_ip_address,
    username='ubuntu',
    key_filename='/root/.ssh/aws-key.pem')

# print('Sending mount file')
# sftp = ssh.open_sftp()
# sftp.put('mount.sh', '/home/ubuntu/mount.sh')
# sftp.close()

print('Executing mount')
stdin, stdout, stderr = ssh.exec_command('sudo bash /home/ubuntu/scirpts/mount.sh')
stdin.flush()
data = stdout.read().splitlines()
print('mount.sh output:')
for line in data:
    print(line)
ssh.close()
print('Okay to connect!')
print('ssh -i ~/.ssh/aws-key.pem ubuntu@{}'.format(public_ip_address))