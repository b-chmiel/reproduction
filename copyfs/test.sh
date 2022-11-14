#!/bin/bash

set -euo

DESTINATION=/mnt
FS_NAME=CopyFS
SEED=420
# -x is not applicable here, it crashes when > 1
BONNIE_ARGS="-d ${DESTINATION} -s 1G -n 15 -m ${FS_NAME} -b -u root -q -z ${SEED}"
OUTPUT_DIRECTORY=/vagrant/out

function setup {
	mkdir -pv /home/vagrant/versions
	mkdir -pv $DESTINATION
	copyfs-mount /home/vagrant/versions $DESTINATION
}

function teardown {
	umount $DESTINATION
}

function test {
	mkdir -pv $OUTPUT_DIRECTORY
	echo "Running bonnie++ benchmark..."

	du -s /home/vagrant/versions >> $OUTPUT_DIRECTORY/versions_size_before.txt
	df >> $OUTPUT_DIRECTORY/df_before.txt
	bonnie++ $BONNIE_ARGS > $OUTPUT_DIRECTORY/out.csv
	df >> $OUTPUT_DIRECTORY/df_after.txt
	du -s /home/vagrant/versions >> $OUTPUT_DIRECTORY/versions_size_after.txt
}

function main {
	setup
	test
	teardown
}

main
