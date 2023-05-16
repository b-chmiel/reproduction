#!/bin/sh

OUTPUT_DIRECTORY=$MOUNT_DIRECTORY/out/tty_runner/validate/

mount_output_directory $OUTPUT_DIRECTORY

remount_nilfs

validate $OUTPUT_DIRECTORY

gen_file --size=10000 --type=0 --seed=420 $MNT_DIR/$FILE2

validate $OUTPUT_DIRECTORY

gen_file --size=2000 --type=0 --seed=420 $MNT_DIR/$FILE1
gen_file --size=2000 --type=0 --seed=420 $MNT_DIR/$FILE2

validate $OUTPUT_DIRECTORY

gen_file --size=1M --type=0 --seed=420 $MNT_DIR/$FILE1
gen_file --size=1M --type=0 --seed=420 $MNT_DIR/$FILE2

validate $OUTPUT_DIRECTORY

umount $MNT_DIR