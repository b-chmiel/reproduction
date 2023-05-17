#!/bin/sh

# set logging level
# echo "1" > /proc/sys/kernel/printk

FS_FILE_SIZE=18G
FS_BIN_FILE=/nilfs2.bin
LOOP_INTERFACE=/dev/loop0
MNT_DIR=/mnt/nilfs2

VALIDATION_ID=0

MOUNT_DIRECTORY=/mnt/work

FILE1=f1
FILE2=f2

function mount_output_directory {
directory=$1

echo "Mounting local folder in ${MOUNT_DIRECTORY}"
mkdir -pv $MOUNT_DIRECTORY
mount -t 9p -o trans=virtio,version=9p2000.L host0 $MOUNT_DIRECTORY
rm -rf $directory
mkdir -pv $directory
}

function mount_nilfs {
rm -f $FS_BIN_FILE
fallocate -l $FS_FILE_SIZE $FS_BIN_FILE
losetup -P $LOOP_INTERFACE $FS_BIN_FILE
mkfs.nilfs2 $LOOP_INTERFACE -B 16
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
