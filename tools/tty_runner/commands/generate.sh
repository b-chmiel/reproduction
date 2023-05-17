#!/bin/sh

OUTPUT_DIRECTORY=$MOUNT_DIRECTORY/out/tty_runner/generate/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

mount_nilfs

validate $OUTPUT_DIRECTORY

gen_file --size=1M --type=0 --seed=420 $MNT_DIR/$FILE1
gen_file --size=1M --type=0 --seed=420 $MNT_DIR/$FILE2

sha512sum $MNT_DIR/$FILE1 > $FILE1.sha512sum
sha512sum $MNT_DIR/$FILE2 > $FILE2.sha512sum

validate $OUTPUT_DIRECTORY

umount $MNT_DIR