#!/bin/sh

OUTPUT_DIRECTORY=$MOUNT_DIRECTORY/out/tty_runner/dedup/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

remount_nilfs

validate $OUTPUT_DIRECTORY

dedup $LOOP_INTERFACE

validate $OUTPUT_DIRECTORY

umount $MNT_DIR