#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source /tests/test_env.sh

fallocate --verbose -l $FILESYSTEM_FILE_SIZE $FILESYSTEM_FILE
modprobe btrfs
mkfs.btrfs $FILESYSTEM_FILE
mkdir -p $DESTINATION
mount $FILESYSTEM_FILE $DESTINATION