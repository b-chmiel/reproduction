#!/bin/bash

set -euo

OUTPUT_DIRECTORY=/vagrant/out/`date +"%Y-%m-%dT%T"`
SEED=420

function setup {
	mkdir -p /mnt/{source,destination}
	wayback -- /mnt/source /mnt/destination
}

function teardown {
	umount /mnt/destination
}

function test {
	mkdir -pv $OUTPUT_DIRECTORY
	echo "Running bonnie++ benchmark..."

	df >> $OUTPUT_DIRECTORY/df_before.txt
	bonnie++ -d /mnt/destination -s 1G -n 15 -m WAYBACKFS -b -u root -q -z $SEED >> $OUTPUT_DIRECTORY/out.csv
	df >> $OUTPUT_DIRECTORY/df_after.txt
}

function main {
	setup
	test
	teardown
}

main
