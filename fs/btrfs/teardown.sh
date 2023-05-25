#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source test_template_env.sh

umount $DESTINATION
rm -fv $FILESYSTEM_FILE
