#!/bin/bash

set -euo

OUTPUT_DIRECTORY=/vagrant/out
FILESYSTEM_FILE=/home/vagrant/nilfs2.bin
SEED=420

function setup {
	fallocate -l 15GiB $FILESYSTEM_FILE
	mkfs -t nilfs2 $FILESYSTEM_FILE
	mkdir -p /mnt
	mount -t nilfs2 $FILESYSTEM_FILE /mnt
}

function teardown {
	umount /mnt
	rm -fv $FILESYSTEM_FILE
}

function test {
	mkdir -pv $OUTPUT_DIRECTORY
	rm -fv $OUTPUT_DIRECTORY/*

	df | grep "/dev/loop0" >> $OUTPUT_DIRECTORY/df_before.txt
	bonnie++ -d /mnt -s 1G -n 15 -m NILFS2 -b -u root -q -z $SEED >> $OUTPUT_DIRECTORY/out.csv
	df | grep "/dev/loop0" >> $OUTPUT_DIRECTORY/df_after.txt
}

function main {
	setup
	test
	teardown
}

main
