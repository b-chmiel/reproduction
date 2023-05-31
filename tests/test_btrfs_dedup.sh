#!/bin/bash

set -euo pipefail

source /tests/test_env.sh

mount_btrfs() {
	rm -fv $FILESYSTEM_FILE

	# commit file removal
	sync

	fallocate --verbose -l $FILESYSTEM_FILE_SIZE $FILESYSTEM_FILE
	modprobe btrfs
	mkfs.btrfs -f $FILESYSTEM_FILE
	mkdir -pv $DESTINATION
	mount $FILESYSTEM_FILE $DESTINATION
}

remount_btrfs() {
	mkdir -pv $DESTINATION
	mount $FILESYSTEM_FILE $DESTINATION
}

umount_btrfs() {
	umount $DESTINATION
}

setup() {
	DIR=$OUTPUT_DIRECTORY/dedup
	TOOL_NAME=$1
	GEN_SIZE=$2

	echo "$TOOL_NAME test with output directory $DIR and gen_size $GEN_SIZE"

	mkdir -pv $DIR

	echo "Generating files for dedup test"
	mount_btrfs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2
	umount_btrfs

	echo "Saving filesystem size after generation"
	remount_btrfs
	df > "$DIR/df_before_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"
}

teardown() {
	TOOL_NAME=$1
	GEN_SIZE=$2

	umount_btrfs

	echo "Saving filesystem size after deduplication"
	remount_btrfs
	df > "$DIR/df_after_deduplication_${TOOL_NAME}_${GEN_SIZE}.txt"
	umount_btrfs

	rm -fv $FILESYSTEM_FILE
}

duperemove_test() {
	GEN_SIZE=$1
	TOOL_NAME=duperemove

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME test and gen_size $GEN_SIZE"
	echo "################################################################################"

	setup $TOOL_NAME $GEN_SIZE
	duperemove -dhrv $DESTINATION/
	teardown $TOOL_NAME $GEN_SIZE
}

dduper_test() {
	GEN_SIZE=$1
	TOOL_NAME=dduper

	echo "################################################################################"
	echo "### Deduplication $TOOL_NAME test and gen_size $GEN_SIZE"
	echo "################################################################################"

	setup $TOOL_NAME $GEN_SIZE
	dduper \
		--device $LOOP_INTERFACE \
		--dir $DESTINATION/ \
		--recurse \
		--chunk-size 4096
	teardown $TOOL_NAME $GEN_SIZE
}

bees_test() {
	GEN_SIZE=$1

	setup bees $GEN_SIZE

	echo "Starting bees deduplication"
	BTRFS_UUID=$(blkid $LOOP_INTERFACE -s UUID -o value)
	cp /tests/beesd.conf /etc/bees/beesd.conf
	sed -i "s/@TO_BE_REPLACED_BY_TEST_SCRIPT@/$BTRFS_UUID/g" /etc/bees/beesd.conf
	(beesd $BTRFS_UUID 2>&1 | tee /var/log/bees.log)&
	sleep 1
	echo "Waiting for bees to finish execution"
	( tail -n0 -f /var/log/bees.log &) | grep -q 'crawl_more ran out of data after'
	echo "Killing bees"
	pkill bees

	teardown bees $GEN_SIZE
	umount /home/vagrant/bees_tmp/bees_mnt/$BTRFS_UUID
}

main() {
	echo "################################################################################"
	echo "################################################################################"
	echo "### TEST_BTRFS_DEDUP"
	echo "################################################################################"
	echo "################################################################################"
	echo ""

	mkdir -pv $OUTPUT_DIRECTORY

	for i in {1..10}
	do
		size=$((2**$i))
		size_str="${size}M"
		duperemove_test $size_str
		dduper_test $size_str
		# bees_test $size_str
	done
}

main