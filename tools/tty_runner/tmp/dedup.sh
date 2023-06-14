#!/bin/sh

OUTPUT_DIRECTORY=$SHARED_DIRECTORY/out/tty_runner/dedup/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

remount_nilfs

validate $OUTPUT_DIRECTORY

dedup -v $LOOP_INTERFACE
umount_nilfs
remount_nilfs

validate $OUTPUT_DIRECTORY

umount_nilfs
remount_nilfs

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY
touch $MNT_DIR/test
run_gc_cleanup

validate $OUTPUT_DIRECTORY

umount_nilfs
