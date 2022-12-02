#!/bin/bash
# This file will be copied to each folder with file system
# and executed in Vagrantbox

set -euo pipefail
IFS=$'\n\t'

DESTINATION=/mnt
SEED=420
FILE_SIZE=1G
BONNIE_ARGS="-d ${DESTINATION} -s ${FILE_SIZE} -n 15 -b -u root -q -z ${SEED}"
FILESYSTEM_FILE=/home/vagrant/fs.bin
OUTPUT_DIRECTORY=/vagrant/out
