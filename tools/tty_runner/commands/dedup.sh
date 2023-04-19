#!/bin/sh

# TEST

# PREREQUISITES

# DESCRIPTION
# 1. perform deduplication on two small files
# 2. check their contents using sha512sum and
# 3. read disk usage before, after deduplication and after first read

# TEST_START

export MNT_DIR=/mnt/nilfs2

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


sh mount_nilfs.sh

gen_file --size=900 --type=0 --seed=420 $MNT_DIR/f1
gen_file --size=900 --type=0 --seed=420 $MNT_DIR/f2

sha512sum $MNT_DIR/f1 > f1.sha512sum
sha512sum $MNT_DIR/f2 > f2.sha512sum

# validate_fs

dedup -v /dev/loop0

# validate_fs

cat $MNT_DIR/f1
cat $MNT_DIR/f2

validate_fs
