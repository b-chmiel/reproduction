#!/bin/bash
# This file will be copied to each folder with file system
# and executed in Vagrantbox

set -euo pipefail

DESTINATION=/mnt
SEED=29047
FILE_SIZE=1G
BLOCK_SIZE=4096
BONNIE_NUMBER_OF_FILES=32
BONNIE_ARGS=(-d ${DESTINATION} -s ${FILE_SIZE}:${BLOCK_SIZE} -n ${BONNIE_NUMBER_OF_FILES} -b -u root -q -z ${SEED})
BONNIE_RUNS=10
FILESYSTEM_FILE=/home/vagrant/fs.bin
FILESYSTEM_FILE_SIZE=20GiB
OUTPUT_DIRECTORY=/vagrant/out
LOOP_INTERFACE=/dev/loop0
DEDUP_TEST_RANGE_END=64

calculate_csum() {
	DIR=$1
	GEN_SIZE=$2

	TIME_FILE="${DIR}/time-csum-calculate.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
	fi

	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			sha512sum $DESTINATION/f1 > $DIR/f1.sha512sum

	# remove new line
	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f1" >> $TIME_FILE

	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			sha512sum $DESTINATION/f2 > $DIR/f2.sha512sum

	# remove new line
	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f2" >> $TIME_FILE
}

validate_csum() {
	DIR=$1
	GEN_SIZE=$2
	WHEN=$3

	TIME_FILE="${DIR}/time-csum-validate.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name,when" > $TIME_FILE
	fi

	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			sha512sum -c $DIR/f1.sha512sum

	# remove new line
	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f1,${WHEN}" >> $TIME_FILE

	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			sha512sum -c $DIR/f2.sha512sum

	# remove new line
	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f2,${WHEN}" >> $TIME_FILE
}
