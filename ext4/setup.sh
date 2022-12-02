#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source test_template_env.sh

fallocate -l 15GiB $FILESYSTEM_FILE
mkfs.ext4 $FILESYSTEM_FILE
mkdir -p $DESTINATION
mount $FILESYSTEM_FILE $DESTINATION
