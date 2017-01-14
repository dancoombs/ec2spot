# ec2spot

Extension of the [fast.ai MOOC](http://course.fast.ai/index.html) setup for use with AWS EC2 spot instances. This code is in development.

## Set-up
Install awscli: http://docs.aws.amazon.com/cli/latest/userguide/installing.html

### Configure

#### Step 1
(Method 1)  Run setup_net.sh to set up VPC, subnets, security group, ssh key. Script sets up these services and copies their AWS IDs to aws.conf for attchement to spot instance. Sets up a 32GB EBS storage to be used at persistent storage when the spot instance is terminated
```bash
cd ec2spot
./setup_net.sh
```
(Method 2)  Use the AWS console to set up:
1. Security group
2. VPC and subnet (must be in us-west-2b)
3. ssh key
4. EBS Volume to be used as persistent storage

Copy ID's of all of the above into aws.conf:
```bash
security_group_id=[AWS SECURITY GROUP ID]
subnet_id=[AWS SUBNET ID]
ssh_key=[NAME OF KEY FILE ON AWS]
ebs_vol_id=[AWS EBS VOLUME ID]
```

#### Step 2
Edit 'instance_type' and 'ami_id' in aws.conf for your desired set-up. Defaults to p2.xlarge and the fast.ai ami.
```bash
instance_type=[DESIRED INSTANCE TYPE]
ami_id=[AWS AMI ID TO BOOT]
```
For convenience, bash aliases have been created to spin up and connect to the EC2 spot instance. To setup, run the following:
```bash
cd ec2spot
cat ec2spot_alias.txt >> ~/.bashrc
cd ~
source .bashrc
```

## Usage

#### Start Spot Instance
To spin up a EC2 spot instance with the configuration settings specified in aws.conf run:
```bash
aws-spot
```

and enter bid price when prompted.

The script works as follows:

1. Submits the bid to the EC2 spot requests. It is recommended to bid over the running price in order to keep your instance running while you are working.

2. Creates a 32GB EBS volume for booting the AMI, this volume gets deleted when the instance is terminated.

3. Attaches the EBS volume specified in the aws.conf file.

4. Copies the script mount.sh over scp and runs it over ssh. This creates a file system in it if one does not exist in the volume, and mounts it to ~/fs 



#### Connect to Instance over ssh
Run:
```bash
aws-ssh
```

A few things to consider while working:

1. All work needs to be done in the ~/fs directory if it is to exist after termination.
2. The instance can be terminated with just 2 minutes of warning if the running price goes above your bid price. Be sure to save your work consistently, and bid high if you would like to stay running.

#### Terminate Instance
Run:
```bash
aws-terminate
```


