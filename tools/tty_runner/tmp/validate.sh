#!/bin/sh

OUTPUT_DIRECTORY=$SHARED_DIRECTORY/out/tty_runner/validate/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

remount_nilfs

validate $OUTPUT_DIRECTORY

nilfs_cleanerd
sleep 3
nilfs-clean --verbose --speed 32
echo 'Waiting for garbage collection end'
tail -n0 -f /var/log/messages | sed '/manual run completed/ q'
echo 'Garbage collection ended'
nilfs-clean --stop
nilfs-clean --quit

umount_nilfs

remount_nilfs
validate $OUTPUT_DIRECTORY
cp $MNT_DIR/$FILE1 $OUTPUT_DIRECTORY/
cp $MNT_DIR/$FILE2 $OUTPUT_DIRECTORY/
umount_nilfs
