#!/bin/bash -ex

echo "STARTING MOUNT" > /root/user_data_mount
echo "STARTING MOUNT"

if [ "x$2" = "x" ]; then echo "missing volume name"; exit -1; fi

ROOT_VOL_ID=$1

export AWS_CREDENTIAL_FILE=/root/.aws.creds
. /root/.aws.creds
export AWS_ACCESS_KEY=$AWSAccessKeyId
export AWS_SECRET_KEY=$AWSSecretKey
export AWS_DEFAULT_REGION=us-west-2

INSTANCE_ID=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

echo ""
echo "Attaching volume ${ROOT_VOL_ID} as /dev/sdf"

# Attach volume
aws ec2 attach-volume --volume-id ${ROOT_VOL_ID} --instance ${INSTANCE_ID} --device /dev/sdf --output text || exit -1

while ! lsblk /dev/xvdf
do
  echo "waiting for device to attach"
  sleep 10
done

echo "Attached /dev/xvdf"

DEVICE=/dev/xvdf1

# specify mounting in /etc/fstab in ami
mount -a
chmod 777 /home/ubuntu/data

echo "END MOUNT" >> /root/user_data_mount
echo "END MOUNT"