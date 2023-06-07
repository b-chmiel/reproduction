#!/bin/bash

set -euo pipefail
set -x

source /tests/test_env.sh
source /vagrant/fs_utils.sh

DIR=$OUTPUT_DIRECTORY/dedup

setup() {
	TOOL_NAME=$1
	GEN_SIZE=$2

	echo "$TOOL_NAME test with output directory $DIR and gen_size $GEN_SIZE"

	mkdir -pv $DIR

	echo "Generating files for dedup test"
	mount_fs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2

	echo "Saving filesystem size after generation"
	remount_fs
	df > "$DIR/df_before_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"
}

teardown() {
	TOOL_NAME=$1
	GEN_SIZE=$2

	echo "Saving filesystem size after deduplication"
	remount_fs
	df > "$DIR/df_after_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"
	destroy_fs
}

duperemove_test() {
	GEN_SIZE=$1
	TOOL_NAME=duperemove

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME test and gen_size $GEN_SIZE"
	echo "################################################################################"

	setup $TOOL_NAME $GEN_SIZE

## TODO
## make profile function instead of repeating time command

	TIME_FILE="${DIR}/time_${TOOL_NAME}_${GEN_SIZE}.log" 
	echo "real-time,system-time,user-time,max-memory" > $TIME_FILE
	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			duperemove \
				-dhrv \
				-b 4096 \
				--dedupe-options=partial,same \
				$DESTINATION/
	teardown $TOOL_NAME $GEN_SIZE
}

dduper_test() {
	GEN_SIZE=$1
	TOOL_NAME=dduper

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME test and gen_size $GEN_SIZE"
	echo "################################################################################"

	setup $TOOL_NAME $GEN_SIZE

	TIME_FILE="${DIR}/time_${TOOL_NAME}_${GEN_SIZE}.log" 
	echo "real-time,system-time,user-time,max-memory" > $TIME_FILE
	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			dduper \
				--device $LOOP_INTERFACE \
				--dir $DESTINATION/ \
				--recurse \
				--chunk-size 4096
	teardown $TOOL_NAME $GEN_SIZE
}

main() {
	echo "################################################################################"
	echo "################################################################################"
	echo "### TEST_BTRFS_DEDUP"
	echo "################################################################################"
	echo "################################################################################"
	echo ""

	mkdir -pv $OUTPUT_DIRECTORY

	for i in $(seq 1 $DEDUP_TEST_RANGE_END); do
		size=$((2**$i))
		size_str="${size}M"
		duperemove_test $size_str
		dduper_test $size_str
	done
}

main