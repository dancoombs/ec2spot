#!/bin/bash -ex

echo "STARTING MOUNT" > /root/user_data_mount
echo "STARTING MOUNT"

if ! [ "x$1" = "x--force" ]
then 
  # this is here just to cover accidental invocation from the command-line. it should "never happen"
  echo "This script is destructive when invoked at the wrong time. If you are seeing this message you are doing something wrong."
  exit -1
fi

if [ "x$2" = "x" ]; then echo "missing volume name"; exit -1; fi

ROOT_VOL_ID=$2

export AWS_CREDENTIAL_FILE=/root/.aws.creds
. /root/.aws.creds
export AWS_ACCESS_KEY=$AWSAccessKeyId
export AWS_SECRET_KEY=$AWSSecretKey

INSTANCE_ID=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

echo ""
echo "Attaching volume ${ROOT_VOL_ID} as /dev/sdf"

# Attach volume
aws ec2 attach-volume --volume-id ${ROOT_VOL_ID} --instance ${INSTANCE_ID} -device /dev/sdf  || exit -1

while ! lsblk /dev/xvdf
do
  echo "waiting for device to attach"
  sleep 10
done

echo "Mounted /dev/xvdf"
echo "Starting root switch"

DEVICE=/dev/xvdf1
NEWMNT=/permaroot
OLDMNT=old-root
e2label $DEVICE permaroot
tune2fs $DEVICE -U `uuidgen`
mkdir $NEWMNT

#
# point of no return... 
# modify /sbin/init on the ephemeral volume to chain-load from the persistent EBS volume, and then reboot.
#
mv /sbin/init /sbin/init.backup
cat >/sbin/init <<EOF
#!/bin/sh
mount $DEVICE $NEWMNT
[ ! -d $NEWMNT/$OLDMNT ] && mkdir -p $NEWMNT/$OLDMNT

cd $NEWMNT
pivot_root . ./$OLDMNT

for dir in /dev /proc /sys /run; do
    echo "Moving mounted file system ${OLDMNT}\${dir} to \$dir."
    mount --move ./${OLDMNT}\${dir} \${dir}
done
exec chroot . /sbin/init
EOF
chmod +x /sbin/init
shutdown -r now

echo "END MOUNT" >> /root/user_data_mount
echo "END MOUNT"