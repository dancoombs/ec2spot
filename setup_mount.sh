#!/bin/bash -ex

echo "STARTING MOUNT" > /root/user_data_mount

if ! [ "x$1" = "x--force" ]
then 
  # this is here just to cover accidental invocation from the command-line. it should "never happen"
  echo "This script is destructive when invoked at the wrong time. If you are seeing this message you are doing something wrong."
  exit -1
fi

if [ "x$2" = "x" ]; then echo "missing volume name"; exit -1; fi

ROOT_VOL_NAME=$2

export AWS_CREDENTIAL_FILE=/root/.aws.creds
. /root/.aws.creds
export AWS_ACCESS_KEY=$AWSAccessKeyId
export AWS_SECRET_KEY=$AWSSecretKey

INSTANCE_ID=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

echo ""
echo "Attaching volume ${ROOT_VOL_ID} as /dev/sdf"

# Attach volume
aws ec2 attach-volume --volume-id ${ROOT_VOL_ID} --instance ${INSTANCE_ID} -device /dev/sdf  || exit -1

echo "END MOUNT" >> /root/user_data_mount