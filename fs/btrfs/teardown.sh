#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source /tests/test_env.sh

umount $DESTINATION
rm -fv $FILESYSTEM_FILE
