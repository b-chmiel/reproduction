#!/bin/bash
# This file will be copied to each folder with file system
# and executed in Vagrantbox

set -euo pipefail

DESTINATION=/mnt
SEED=29047
FILE_SIZE=1G
BLOCK_SIZE=4096
BONNIE_NUMBER_OF_FILES=32
BONNIE_ARGS=(-d ${DESTINATION} -s ${FILE_SIZE}:${BLOCK_SIZE} -n ${BONNIE_NUMBER_OF_FILES} -b -u root -q -z ${SEED})
DELETION_TEST_TRIALS=3
FILESYSTEM_FILE=/home/vagrant/fs.bin
FILESYSTEM_FILE_SIZE=15GiB
OUTPUT_DIRECTORY=/vagrant/out
LOOP_INTERFACE=/dev/loop0
DEDUP_TEST_RANGE_END=10
