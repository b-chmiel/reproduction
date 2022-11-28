#!/bin/bash

set -euo pipefail

source test_template_env.sh

umount $DESTINATION
rm -fv $FILESYSTEM_FILE
