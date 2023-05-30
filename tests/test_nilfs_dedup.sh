#!/bin/bash

set -euo pipefail

source /tests/test_env.sh

mount_nilfs() {
	echo "Mounting nilfs at $DESTINATION"
	rm -f $FILESYSTEM_FILE
	fallocate -l $FILESYSTEM_FILE_SIZE $FILESYSTEM_FILE
	mkfs -t nilfs2 $FILESYSTEM_FILE
	mkdir -p $DESTINATION
	mount -i -v -t nilfs2 $FILESYSTEM_FILE $DESTINATION
	nilfs-tune -i 1 $LOOP_INTERFACE
}

remount_nilfs() {
	echo "Remounting nilfs to $DESTINATION"
	mount -i -v -t nilfs2 $FILESYSTEM_FILE $DESTINATION
}

umount_nilfs() {
	echo "Unmounting nilfs from $DESTINATION"
busy=true
while $busy
do
 if mountpoint -q $DESTINATION
 then
  umount $DESTINATION 2> /dev/null
  if [ $? -eq 0 ]
  then
   busy=false  # umount successful
  else
   echo '.'  # output to show that the script is alive
   sleep 5      # 5 seconds for testing, modify to 300 seconds later on
  fi
 else
  busy=false  # not mounted
 fi
done
	echo "Unmount completed"
}

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

	echo "Deduplication test with output directory $DIR and gen_size $GEN_SIZE"

	mkdir -pv $DIR

	umount_nilfs || true

	echo "Generating files for dedup test"
	mount_nilfs
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f1
	genfile --size=$GEN_SIZE --type=0 --seed=$SEED $DESTINATION/f2
	umount_nilfs

	echo "Saving filesystem size after generation"
	remount_nilfs
	df > $DIR/df_before_deduplication_dedup_$GEN_SIZE.txt
	dedup -v $LOOP_INTERFACE
	umount_nilfs

	remount_nilfs
	run_gc_cleanup
	umount_nilfs

	echo "Saving filesystem size after deduplication"
	remount_nilfs
	df > $DIR/df_after_deduplication_dedup_$GEN_SIZE.txt
	umount_nilfs

	rm -fv $FILESYSTEM_FILE
}

main() {
	mkdir -pv $OUTPUT_DIRECTORY

	for i in {2..6}
	do
		size=$((2**$i))
		size_str="${size}M"
		dedup_test $size_str
	done
}

main