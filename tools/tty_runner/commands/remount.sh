#!/bin/sh

# TEST

# PREREQUISITES
# - dedup.sh

# DESCRIPTION
# on previously deduped fs validate if files are stored correctly and
# check fs disk usage

# TEST_START

export MNT_DIR=/mnt/nilfs2
export FS_FILE_SIZE=500M
export FS_BIN_FILE=/nilfs2.bin
export LOOP_INTERFACE=/dev/loop0

# since 'du' does not have '-b' argument
# in-house solution is needed
# https://superuser.com/a/1158437/1780577
function dir_size {
directory=$1
ls -al $directory | awk 'BEGIN {tot=0;} {tot = tot + $5;} END {printf ("%d\n",tot);}'
}

function validate_fs {
echo "$MNT_DIR SIZE"
dir_size $MNT_DIR

echo "CHECKSUM VALIDATION"
sha512sum -c f1.sha512sum
sha512sum -c f2.sha512sum
}

losetup -P $LOOP_INTERFACE $FS_BIN_FILE
mkdir -p $MNT_DIR
mount -t nilfs2 $LOOP_INTERFACE $MNT_DIR

# validate_fs

cat $MNT_DIR/f1
cat $MNT_DIR/f2

validate_fs