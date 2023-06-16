#!/bin/bash

set -euo pipefail
set -x

source /tests/test_env.sh
source /vagrant/fs_utils.sh

setup() {
	TOOL_NAME=$1
	GEN_SIZE=$2
	DIR=$3

	echo "$TOOL_NAME test with output directory $DIR and gen_size $GEN_SIZE"

	echo "Generating files for dedup test"
	mount_fs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2

	echo "Saving filesystem size after generation"
	remount_fs
	df > "$DIR/df_before_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"

	calculate_csum $DIR $GEN_SIZE
	validate_csum $DIR $GEN_SIZE before
}

setup_not_same() {
	TOOL_NAME=$1
	GEN_SIZE=$2
	DIR=$3

	echo "$TOOL_NAME test with output directory $DIR and gen_size $GEN_SIZE"

	echo "Generating files for dedup test"
	mount_fs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2
	echo 'a' >> $DESTINATION/f1
	echo 'b' >> $DESTINATION/f2

	echo "Saving filesystem size after generation"
	remount_fs
	df > "$DIR/df_before_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"

	calculate_csum $DIR $GEN_SIZE
	validate_csum $DIR $GEN_SIZE before
}

teardown() {
	TOOL_NAME=$1
	GEN_SIZE=$2
	DIR=$3

	echo "Saving filesystem size after deduplication"
	remount_fs
	df > "$DIR/df_after_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"
	validate_csum $DIR $GEN_SIZE after
	destroy_fs
}

duperemove_test() {
	GEN_SIZE=$1
	TOOL_NAME=duperemove
	DIR=$OUTPUT_DIRECTORY/dedup/duperemove

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME test and gen_size $GEN_SIZE"
	echo "################################################################################"

	mkdir -pv $DIR
	setup $TOOL_NAME $GEN_SIZE $DIR

## TODO
## make profile function instead of repeating time command

	TIME_FILE="${DIR}/time-whole.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
	fi
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

	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f" >> $TIME_FILE

	teardown $TOOL_NAME $GEN_SIZE $DIR
}

duperemove_not_same_test() {
	GEN_SIZE=$1
	TOOL_NAME=duperemove
	DIR=$OUTPUT_DIRECTORY/dedup/duperemove_not-same

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME not same test and gen_size $GEN_SIZE"
	echo "################################################################################"

	mkdir -pv $DIR
	setup_not_same $TOOL_NAME $GEN_SIZE $DIR

## TODO
## make profile function instead of repeating time command

	TIME_FILE="${DIR}/time-whole.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
	fi
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

	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f" >> $TIME_FILE

	teardown $TOOL_NAME $GEN_SIZE $DIR
}

dduper_test() {
	GEN_SIZE=$1
	TOOL_NAME=dduper
	DIR=$OUTPUT_DIRECTORY/dedup/dduper

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME test and gen_size $GEN_SIZE"
	echo "################################################################################"

	mkdir -pv $DIR
	setup $TOOL_NAME $GEN_SIZE $DIR

	TIME_FILE="${DIR}/time-whole.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
	fi
	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			dduper \
				--device $LOOP_INTERFACE \
				--dir $DESTINATION/ \
				--recurse \
				--chunk-size 128

	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f" >> $TIME_FILE

	teardown $TOOL_NAME $GEN_SIZE $DIR
}

dduper_not_same_test() {
	GEN_SIZE=$1
	TOOL_NAME=dduper
	DIR=$OUTPUT_DIRECTORY/dedup/dduper_not-same

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME not same test and gen_size $GEN_SIZE"
	echo "################################################################################"

	mkdir -pv $DIR

	setup_not_same $TOOL_NAME $GEN_SIZE $DIR

	TIME_FILE="${DIR}/time-whole.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
	fi
	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			dduper \
				--device $LOOP_INTERFACE \
				--dir $DESTINATION/ \
				--recurse \
				--chunk-size 128

	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f" >> $TIME_FILE

	teardown $TOOL_NAME $GEN_SIZE $DIR
}

main() {
	echo "################################################################################"
	echo "################################################################################"
	echo "### TEST_BTRFS_DEDUP"
	echo "################################################################################"
	echo "################################################################################"
	echo ""

	mkdir -pv $OUTPUT_DIRECTORY

	for i in $(seq 1 3); do
		size=$((2**$i))
		size_str="${size}M"
		duperemove_test $size_str
		dduper_test $size_str
		duperemove_not_same_test $size_str
		dduper_not_same_test $size_str
	done

	for i in $(seq 1 $DEDUP_TEST_RANGE_END); do
		size=$((16*$i))
		size_str="${size}M"
		duperemove_test $size_str
		dduper_test $size_str
		duperemove_not_same_test $size_str
		dduper_not_same_test $size_str
	done
}

main