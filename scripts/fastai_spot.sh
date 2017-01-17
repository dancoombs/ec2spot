#!/bin/bash

if [ "$1" = "" ]; then echo "ERROR: please specify a configuration file
Usage: fastai_spot.sh *.conf bid"; exit -1; fi
. $1 || exit -1

echo 'Enter bid, followed by [ENTER]: '

read bid_price

cat >specs.tmp <<EOF
{
  "KeyName" : "$ssh_key",
  "InstanceType": "$instance_type",
  "ImageId" : "$ami_id",
  "Placement": {
    "AvailabilityZone": "us-west-2b"
  },
  "NetworkInterfaces": [
  {
    "DeviceIndex": 0,
    "SubnetId": "$subnet_id",
    "Groups": [ "$security_group_id" ],
    "AssociatePublicIpAddress": true
  }],
  "BlockDeviceMappings": [
    {
      "DeviceName" : "/dev/sda1",
      "Ebs": {
        "VolumeSize": 32,
        "DeleteOnTermination": true,
        "VolumeType" : "gp2"
      }
    }
  ]
}
EOF

export requestId=`aws ec2 request-spot-instances --spot-price ${bid_price} --type 'one-time' --launch-specification file://specs.tmp --query "SpotInstanceRequests[0].SpotInstanceRequestId" --output text`

echo 'Waiting for request, if taking long increase bid price'
aws ec2 wait spot-instance-request-fulfilled --spot-instance-request-ids $requestId

# get instance id
export instanceId=`aws ec2 describe-spot-instance-requests --spot-instance-request-ids $requestId  --query "SpotInstanceRequests[0].InstanceId" --output text`
echo InstanceId: $instanceId

echo 'Wait for instance running'
aws ec2 wait instance-running --instance-ids $instanceId

echo Attaching volume: $ebs_vol_id
aws ec2 attach-volume --volume-id $ebs_vol_id --instance-id $instanceId --device /dev/sdf

echo 'Waiting for volume attach'
aws ec2 wait volume-in-use --volume-id $ebs_vol_id

# get ip
export aws_ip=`aws ec2 describe-instances  --instance-ids $instanceId --query "Reservations[0].Instances[0].PublicIpAddress" --output text`
echo Connect: ssh -i ~/.ssh/aws-key.pem ubuntu@$aws_ip

echo 'Waiting instance ok, takes a few minutes'
aws ec2 wait instance-status-ok --instance-ids $instanceId

echo 'SSH to mount volume located at /dev/xvdf to /home/ubuntu/data'
scp -i '~/.ssh/aws-key.pem' ~/ec2spot/mount.sh ubuntu@$aws_ip:~
ssh -i '~/.ssh/aws-key.pem' ubuntu@$aws_ip 'sudo bash mount.sh'

echo 'Done'