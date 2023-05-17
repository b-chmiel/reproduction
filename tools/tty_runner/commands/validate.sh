#!/bin/sh

OUTPUT_DIRECTORY=$MOUNT_DIRECTORY/out/tty_runner/validate/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

remount_nilfs

# before
validate $OUTPUT_DIRECTORY

gen_file --size=10000 --type=0 --seed=420 $MNT_DIR/$FILE2

# after_modification_of_second_file
validate $OUTPUT_DIRECTORY

umount $MNT_DIR
remount_nilfs

# after_modification_of_second_file_after_remount
validate $OUTPUT_DIRECTORY

gen_file --size=1M --type=0 --seed=420 $MNT_DIR/$FILE2

# after_restoring_second_file
validate $OUTPUT_DIRECTORY

umount $MNT_DIR
remount_nilfs

# after_restoring_second_file_after_remount
validate $OUTPUT_DIRECTORY

gen_file --size=1000 --type=0 --seed=420 $MNT_DIR/$FILE1

# after_changing_first_file
validate $OUTPUT_DIRECTORY

umount $MNT_DIR
remount_nilfs

# after_changing_first_file_after_remount
validate $OUTPUT_DIRECTORY

gen_file --size=1M --type=0 --seed=420 $MNT_DIR/$FILE1

# after_restoring_first_file
validate $OUTPUT_DIRECTORY

umount $MNT_DIR
remount_nilfs

# after_restoring_first_file_after_remount
validate $OUTPUT_DIRECTORY