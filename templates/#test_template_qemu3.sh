#!/bin/bash
# This file will be copied to qemu and executed

set -euo pipefail

DESTINATION=/mnt/nilfs2
SEED=420
FILE_SIZE=1G
BONNIE_ARGS="-d ${DESTINATION} -s ${FILE_SIZE} -n 15 -b -u root -q -z ${SEED}"
FILESYSTEM_FILE=/nilfs2.bin
MOUNT_DIRECTORY=/mnt/work
OUTPUT_DIRECTORY="${MOUNT_DIRECTORY}/out"
FS_NAME=nilfs-dedup
LOOP_INTERFACE=/dev/loop0

prepare_mount_point() {
	echo "Mounting local folder in ${MOUNT_DIRECTORY}"
	mkdir -pv $MOUNT_DIRECTORY
	mount -t 9p -o trans=virtio,version=9p2000.L host0 $MOUNT_DIRECTORY
}

remount_filesystem() {
    losetup -P $LOOP_INTERFACE $FILESYSTEM_FILE
    mkdir -p $DESTINATION
    mount -t nilfs2 $LOOP_INTERFACE $DESTINATION
}

setup() {
    mkdir -pv $OUTPUT_DIRECTORY
	prepare_mount_point
	remount_filesystem
}

bonnie_test() {
	echo "Preparing bonnie++ benchmark..."

    DIR=$OUTPUT_DIRECTORY/bonnie
    mkdir -pv $DIR

    echo "Running bonnie++ benchmark..."

    df >> $DIR/df_before_bonnie.txt
    bonnie++ $BONNIE_ARGS -m $FS_NAME >> $DIR/out.csv
    df >> $DIR/df_after_bonnie.txt
}

fio_test() {
	echo "Preparing fio benchmark..."

    DIR=$OUTPUT_DIRECTORY/fio
    mkdir -pv $DIR

	echo $MOUNT_DIRECTORY
	echo $DESTINATION

    cp -v $MOUNT_DIRECTORY/fio-job.cfg $DESTINATION/fio-job.cfg
	
	echo "Running fio benchmark..."
    cd $DESTINATION
        df >> $DIR/df_before_fio_file_append_read_test.txt
        fio fio-job.cfg --section file_append_read_test
        df >> $DIR/df_after_fio_file_append_read_test.txt

        df >> $DIR/df_before_fio_file_append_write_test.txt
        fio fio-job.cfg --section file_append_write_test
        df >> $DIR/df_after_fio_file_append_write_test.txt

        df >> $DIR/df_before_fio_random_read_test.txt
        fio fio-job.cfg --section random_read_test
        df >> $DIR/df_after_fio_random_read_test.txt

        df >> $DIR/df_before_fio_random_write_test.txt
        fio fio-job.cfg --section random_write_test
        df >> $DIR/df_after_fio_random_write_test.txt

        mv *.log $DIR/
    cd ..
}

delete_test() {
    TRIALS=2
    TEST_FILE=delete_test_file
    DIR=$OUTPUT_DIRECTORY/delete
	echo "Preparing deletion test..."
    mkdir -pv $DIR

    echo "Running deletion test for: ${TRIALS} trials"

    df >> $DIR/df_before_delete_test.txt
    cd $DESTINATION
	counter=1
	while [ $counter -le ${TRIALS} ]
        do
	    echo "Trial ${counter} / ${TRIALS}"
	
            gen_file --size=1G --seed=$SEED $TEST_FILE
            rm -fv $TEST_FILE
	    counter=$((counter+1))
        done
    cd ..
    df >> $DIR/df_after_delete_test.txt
}

teardown() {
	umount $DESTINATION
}

main() {
	setup

    bonnie_test
    # fio_test
    # delete_test

	teardown
}

main