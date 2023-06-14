#!/bin/sh

# set logging level
echo "5" > /proc/sys/kernel/printk

FS_FILE_SIZE=18G
FS_BIN_FILE=/nilfs2.bin
LOOP_INTERFACE=/dev/loop0
MNT_DIR=/mnt/nilfs2
SEED=420
FILE1=f1
FILE2=f2
SHARED_DIRECTORY=/mnt/work
GEN_SIZE=64M

VALIDATION_ID=0

function mount_output_directory {
directory=$1
echo "Mounting local folder in ${SHARED_DIRECTORY}"
mkdir -pv $SHARED_DIRECTORY
mount -t 9p -o trans=virtio,version=9p2000.L host0 $SHARED_DIRECTORY
rm -rf $directory
mkdir -pv $directory
}

function mount_nilfs {
rm -f $FS_BIN_FILE
fallocate -l $FS_FILE_SIZE $FS_BIN_FILE
losetup -P $LOOP_INTERFACE $FS_BIN_FILE
mkfs.nilfs2 $LOOP_INTERFACE
nilfs-tune -i 1 $LOOP_INTERFACE
mkdir -p $MNT_DIR
mount -t nilfs2 $LOOP_INTERFACE $MNT_DIR
}

function remount_nilfs {
losetup -P $LOOP_INTERFACE $FS_BIN_FILE
mkdir -p $MNT_DIR
mount -t nilfs2 $LOOP_INTERFACE $MNT_DIR
}

function dirsize {
directory=$1
df | grep $directory
}

function validate_checksum {
directory=$1
sha512sum -c $FILE1.sha512sum | tee $directory/validate_${VALIDATION_ID}_checksum_$FILE1
sha512sum -c $FILE2.sha512sum | tee $directory/validate_${VALIDATION_ID}_checksum_$FILE2
}

function validate {
directory=$1
dirsize $MNT_DIR | tee $directory/validate_${VALIDATION_ID}_dirsize

lssu | tee $directory/validate_${VALIDATION_ID}_lssu
lscp | tee $directory/validate_${VALIDATION_ID}_lscp

validate_checksum $directory

VALIDATION_ID=$(($VALIDATION_ID + 1))
}

function umount_nilfs {
echo 'Umounting nilfs'
busy=true
while $busy
do
 if mountpoint -q $MNT_DIR
 then
  umount $MNT_DIR 2> /dev/null
  if [ $? -eq 0 ]
  then
   busy=false  # umount successful
  else
   echo '.'  # output to show that the script is alive
   sleep 5      # 5 seconds for testing, modify to 300 seconds later on
  fi
 else
  busy=false  # not mounted
 fi
done
}

function run_gc_cleanup {
nilfs_cleanerd
sleep 3
nilfs-clean -p 0 -m 0 --verbose --speed 32
echo 'Waiting for garbage collection end'
tail -n0 -f /var/log/messages | sed '/manual run completed/ q'
echo 'Garbage collection ended'
nilfs-clean --stop
nilfs-clean --quit
}
