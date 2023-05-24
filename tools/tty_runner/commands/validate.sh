#!/bin/sh

OUTPUT_DIRECTORY=$SHARED_DIRECTORY/out/tty_runner/validate/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

remount_nilfs

# before
validate $OUTPUT_DIRECTORY

gen_file --size=$GEN_SIZE --type=0 --seed=123 $MNT_DIR/$FILE2

# after_modification_of_second_file
validate $OUTPUT_DIRECTORY

umount_nilfs
remount_nilfs

# after_modification_of_second_file_after_remount
validate $OUTPUT_DIRECTORY

gen_file --size=$GEN_SIZE --type=0 --seed=$SEED $MNT_DIR/$FILE2

# after_restoring_second_file
validate $OUTPUT_DIRECTORY

umount_nilfs
remount_nilfs

# after_restoring_second_file_after_remount
validate $OUTPUT_DIRECTORY

gen_file --size=$GEN_SIZE --type=0 --seed=1234 $MNT_DIR/$FILE1

# after_changing_first_file
validate $OUTPUT_DIRECTORY

umount_nilfs
remount_nilfs

# after_changing_first_file_after_remount
validate $OUTPUT_DIRECTORY

gen_file --size=$GEN_SIZE --type=0 --seed=$SEED $MNT_DIR/$FILE1

# after_restoring_first_file
validate $OUTPUT_DIRECTORY

umount_nilfs
remount_nilfs

# after_restoring_first_file_after_remount
validate $OUTPUT_DIRECTORY

umount_nilfs