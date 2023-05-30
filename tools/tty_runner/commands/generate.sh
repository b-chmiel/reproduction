#!/bin/sh

OUTPUT_DIRECTORY=$SHARED_DIRECTORY/out/tty_runner/generate/

mount_output_directory $OUTPUT_DIRECTORY

echo '1' > $OUTPUT_DIRECTORY/started

mount_nilfs

validate $OUTPUT_DIRECTORY

genfile --size=$GEN_SIZE --type=0 --seed=$SEED $MNT_DIR/$FILE1
genfile --size=$GEN_SIZE --type=0 --seed=$SEED $MNT_DIR/$FILE2

sha512sum $MNT_DIR/$FILE1 > $FILE1.sha512sum
sha512sum $MNT_DIR/$FILE2 > $FILE2.sha512sum

validate $OUTPUT_DIRECTORY

umount_nilfs