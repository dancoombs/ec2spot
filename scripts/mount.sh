mkdir /home/ubuntu/fs
echo 'Checking for file system'

if ! [[ $( blkid /dev/xvdf -s TYPE -o value ) = 'ext4' ]]; then
	echo 'No file system detected, making ext4'
	mkfs -t ext4 /dev/xvdf
else
	echo 'Found file system'
fi

echo 'Mounting /dev/xvdf to /home/ubuntu/fs'
mount /dev/xvdf /home/ubuntu/fs
chmod 777 fs
echo 'Done'