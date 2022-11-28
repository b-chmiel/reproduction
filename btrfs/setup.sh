#!/bin/bash

set -euo pipefail

source test_template_env.sh

fallocate -l 15GiB $FILESYSTEM_FILE
modprobe btrfs
mkfs.btrfs $FILESYSTEM_FILE
mkdir -p $DESTINATION
mount $FILESYSTEM_FILE $DESTINATION
