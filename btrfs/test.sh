#!/bin/bash

set -euo

DESTINATION=/mnt
FS_NAME=BTRFS
SEED=420
BONNIE_ARGS="-d ${DESTINATION} -s 1G -n 15 -m ${FS_NAME} -b -u root -q -z ${SEED}"
FILESYSTEM_FILE=/home/vagrant/fs.bin
OUTPUT_DIRECTORY=/vagrant/out

function setup {
	fallocate -l 15GiB $FILESYSTEM_FILE
	modprobe btrfs
	mkfs.btrfs $FILESYSTEM_FILE
	mkdir -p $DESTINATION
	mount $FILESYSTEM_FILE $DESTINATION
}

function teardown {
	umount $DESTINATION
	rm -fv $FILESYSTEM_FILE
}

function test {
	mkdir -pv $OUTPUT_DIRECTORY
	echo "Running bonnie++ benchmark..."

	df >> $OUTPUT_DIRECTORY/df_before.txt
	bonnie++ $BONNIE_ARGS >> $OUTPUT_DIRECTORY/out.csv
	df >> $OUTPUT_DIRECTORY/df_after.txt
}

function main {
	setup
	test
	teardown
}

main
