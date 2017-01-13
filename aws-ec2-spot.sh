#!/bin/bash

if [ "$1" = "" ]; then echo "USER ERROR: please specify a configuration file"; exit -1; fi

. $1 || exit -1
ROOT_VOL_ID=$ec2spotter_volume_name

echo "ROOT_VOL_ID=${ROOT_VOL_ID}"

cat >user-data.tmp <<EOF
#!/bin/bash -ex

echo "STARTING USER DATA" > /root/user_data_run

echo AWSAccessKeyId=$aws_access_key > /root/.aws.creds
echo AWSSecretKey=$aws_secret_key >> /root/.aws.creds

cd /root

git clone https://$git_username:$git_password@github.com/dancoombs/ec2spot.git

cd ec2spot

apt-get update
apt-get install -y python-pip python-setuptools
pip install awscli

./setup_mount.sh --force ${ROOT_VOL_ID}

echo "END USER DATA" >> /root/user_data_run
EOF

userData=$(base64 user-data.tmp | tr -d '\n');

cat >specs.tmp <<EOF
{
  "KeyName" : "$ssh_key",
  "InstanceType": "$ec2spotter_instance_type",
  "ImageId" : "$ec2spotter_preboot_image_id",
  "UserData" : "${userData}",
  "Placement": {
    "AvailabilityZone": "us-west-2b"
  },
  "NetworkInterfaces": [
  {
    "DeviceIndex": 0,
    "SubnetId": "subnet-c558bc8c",
    "Groups": [ "sg-c7c132bf" ],
    "AssociatePublicIpAddress": true
  }],
  "BlockDeviceMappings": [
    {
      "DeviceName" : "/dev/sda1",
      "Ebs": {
        "VolumeSize": 8,
        "DeleteOnTermination": true,
        "VolumeType" : "gp2"
      }
    }
  ]
}
EOF

aws ec2 request-spot-instances --spot-price $ec2spotter_bid_price --type 'one-time' --launch-specification file://specs.tmp > out.txt

