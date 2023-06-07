#!/bin/bash

set -euo pipefail
set -x

source /tests/test_env.sh
source /vagrant/fs_utils.sh

run_gc_cleanup() {
	echo "Running gc cleanup"
	echo "Launching cleanerd daemon"
	nilfs_cleanerd
	sleep 3
	echo "Cleaning"
	nilfs-clean -p 0 -m 0 --verbose --speed 32
	echo 'Waiting for garbage collection end'
	( tail -n0 -f /var/log/daemon.log &) | grep -q 'manual run completed'
	echo 'Garbage collection ended'
	nilfs-clean --stop
	nilfs-clean --quit
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

	echo "Saving filesystem size after generation"
	remount_fs
	df > $DIR/df_before_deduplication_dedup_$GEN_SIZE.txt

	TIME_FILE="${DIR}/time_nilfs-dedup_${GEN_SIZE}.log" 
	echo "real-time,system-time,user-time,max-memory" > $TIME_FILE
	/usr/bin/time \
		--format='%e,%S,%U,%M' \
		--append \
		--output=$TIME_FILE \
		-- \
			dedup -v $LOOP_INTERFACE

	remount_fs
	run_gc_cleanup

	echo "Saving filesystem size after deduplication"
	remount_fs
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

	for i in $(seq 1 $DEDUP_TEST_RANGE_END); do
		size=$((2**$i))
		size_str="${size}M"
		dedup_test $size_str
	done
}

main