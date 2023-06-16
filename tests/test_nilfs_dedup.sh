#!/bin/bash

set -euo pipefail
set -x

source /tests/test_env.sh
source /vagrant/fs_utils.sh

deduplicate() {
	DIR=$1
	GEN_SIZE=$2

	TIME_FILE="${DIR}/time-whole.csv"

	if [ ! -f $TIME_FILE ]; then
		echo "real-time,system-time,user-time,max-memory,file-size,file-name" > $TIME_FILE
	fi

	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			sudo bash /tests/nilfs_dedup_run_dedup.sh $DIR $GEN_SIZE
	
	truncate -s -1 $TIME_FILE
	echo ",${GEN_SIZE},f" >> $TIME_FILE
}

dedup_test() {
	DIR=$OUTPUT_DIRECTORY/dedup
	GEN_SIZE=$1

	echo "################################################################################"
	echo "### Deduplication test with output directory $DIR and gen_size $GEN_SIZE"
	echo "################################################################################"

	mkdir -pv $DIR

	echo "Generating files for dedup test"
	mount_fs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2
	run_gc_cleanup

	echo "Saving filesystem size after generation"
	remount_fs

	calculate_csum $DIR $GEN_SIZE
	validate_csum $DIR $GEN_SIZE before

	df > $DIR/df_before_deduplication_dedup_$GEN_SIZE.txt

	deduplicate $DIR $GEN_SIZE

	echo "Saving filesystem size after deduplication"
	remount_fs

	validate_csum $DIR $GEN_SIZE after

	df > $DIR/df_after_deduplication_dedup_$GEN_SIZE.txt
	destroy_fs
}

dedup_test_not_same() {
	DIR=$OUTPUT_DIRECTORY/dedup-not-same
	GEN_SIZE=$1

	echo "################################################################################"
	echo "### Deduplication test not same with output directory $DIR and gen_size $GEN_SIZE"
	echo "################################################################################"

	mkdir -pv $DIR

	echo "Generating files for dedup test"
	mount_fs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2
	echo 'a' >> $DESTINATION/f1
	echo 'b' >> $DESTINATION/f2
	run_gc_cleanup

	echo "Saving filesystem size after generation"
	remount_fs

	calculate_csum $DIR $GEN_SIZE
	validate_csum $DIR $GEN_SIZE before

	df > $DIR/df_before_deduplication_dedup_$GEN_SIZE.txt

	deduplicate $DIR $GEN_SIZE

	echo "Saving filesystem size after deduplication"
	remount_fs

	validate_csum $DIR $GEN_SIZE after

	df > $DIR/df_after_deduplication_dedup_$GEN_SIZE.txt
	destroy_fs
}

main() {
	echo "################################################################################"
	echo "################################################################################"
	echo "### TEST_NILFS_DEDUP"
	echo "################################################################################"
	echo "################################################################################"
	echo ""

	mkdir -pv $OUTPUT_DIRECTORY

	for i in $(seq 1 3); do
		size=$((2**$i))
		size_str="${size}M"
		dedup_test $size_str
		dedup_test_not_same $size_str
	done

	for i in $(seq 1 $DEDUP_TEST_RANGE_END); do
		size=$((16*$i))
		size_str="${size}M"
		dedup_test $size_str
		dedup_test_not_same $size_str
	done
}

main