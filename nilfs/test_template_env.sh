#!/bin/bash
# This file will be copied to each folder with file system
# and executed in Vagrantbox

set -euo pipefail

DESTINATION=/mnt
SEED=420
BONNIE_ARGS="-d ${DESTINATION} -s 1G -n 15 -b -u root -q -z ${SEED}"
FILESYSTEM_FILE=/home/vagrant/fs.bin
OUTPUT_DIRECTORY=/vagrant/out
