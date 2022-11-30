#!/bin/bash

set -euo pipefail

source test_template_env.sh

fallocate -l 15GiB $FILESYSTEM_FILE
mkfs -t nilfs2 $FILESYSTEM_FILE
mkdir -pv $DESTINATION
mount -i -v -t nilfs2 $FILESYSTEM_FILE $DESTINATION
