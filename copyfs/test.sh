#!/bin/bash

set -euo

OUTPUT_DIRECTORY=/vagrant/out
SEED=420

function setup {
	mkdir -pv /home/vagrant/versions
	mkdir -pv /mnt

	copyfs-mount /home/vagrant/versions /mnt
}

function teardown {
	umount /mnt
}

function test {
	mkdir -pv $OUTPUT_DIRECTORY
	rm -fv $OUTPUT_DIRECTORY/*

	du -s /home/vagrant/versions >> $OUTPUT_DIRECTORY/versions_size_before.txt
	df >> $OUTPUT_DIRECTORY/df_before.txt
	bonnie++ -d /mnt -s 1G -n 15 -m COPYFS -b -u root -q -z $SEED >> $OUTPUT_DIRECTORY/out.csv
	df >> $OUTPUT_DIRECTORY/df_after.txt
	du -s /home/vagrant/versions >> $OUTPUT_DIRECTORY/versions_size_after.txt
}

function main {
	setup
	test
	teardown
}

main
