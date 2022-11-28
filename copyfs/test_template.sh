#!/bin/bash

# This file will be copied to each folder with file system
# and executed in Vagrantbox

set -euo pipefail

if [[ $# -eq 0 ]] ; then
    echo 'Test template need fs_name argument'
    exit 1
fi

FS_NAME=$1

source test_template_env.sh

mkdir -pv $OUTPUT_DIRECTORY
echo "Running bonnie++ benchmark..."

df >> $OUTPUT_DIRECTORY/df_before.txt
bonnie++ $BONNIE_ARGS -m $FS_NAME >> $OUTPUT_DIRECTORY/out.csv
df >> $OUTPUT_DIRECTORY/df_after.txt
