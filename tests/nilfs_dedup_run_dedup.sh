#!/bin/bash

set -euo pipefail
set -x

source /tests/test_env.sh
source /vagrant/fs_utils.sh

DIR=$1
GEN_SIZE=$2

TIME_FILE="${DIR}/time_nilfs-dedup.csv"

if [ ! -f $TIME_FILE ]; then
	echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
fi

/usr/bin/time \
	--format='%e,%S,%U,%M' \
	--append \
	--output=$TIME_FILE \
	-- \
		dedup -v $LOOP_INTERFACE

# remove new line
truncate -s -1 $TIME_FILE
echo ",${GEN_SIZE},f" >> $TIME_FILE

touch $DESTINATION/file
run_gc_cleanup
touch $DESTINATION/file
run_gc_cleanup
touch $DESTINATION/file
run_gc_cleanup