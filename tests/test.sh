#!/bin/bash

set -euo pipefail
set -x

if [[ $# -eq 0 ]] ; then
    echo 'Test template need fs_name argument'
    exit 1
fi

FS_NAME=$1

source /tests/test_env.sh
source /vagrant/fs_utils.sh

bonnie_test() {
    DIR=$OUTPUT_DIRECTORY/bonnie

	echo "################################################################################"
	echo "### Bonnie++ test for args ${BONNIE_ARGS[@]} and output directory $DIR"
	echo "################################################################################"

    mkdir -pv $DIR

    mount_fs
    df >> $DIR/df_before_bonnie.txt
    bonnie++ "${BONNIE_ARGS[@]}" -m $FS_NAME >> $DIR/out.csv
    remount_fs
    df >> $DIR/df_after_bonnie.txt
    destroy_fs
    sleep 5
    destroy_fs
}

fio_test() {
    DIR=$OUTPUT_DIRECTORY/fio
    CFG_FILE=fio-job.cfg

	echo "################################################################################"
	echo "### Fio test for cfg file $CFG_FILE, output directory $DIR"
	echo "################################################################################"

    mkdir -pv $DIR

    mount_fs
    df >> $DIR/df_before_fio_file_append_read_test.txt
    pushd $DESTINATION
        fio /tests/$CFG_FILE --section file_append_read_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_file_append_read_test.txt
    destroy_fs

    mount_fs
    df >> $DIR/df_before_fio_file_append_write_test.txt
    pushd $DESTINATION
        fio /tests/$CFG_FILE --section file_append_write_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_file_append_write_test.txt
    destroy_fs

    mount_fs
    df >> $DIR/df_before_fio_random_read_test.txt
    pushd $DESTINATION
        fio /tests/$CFG_FILE --section random_read_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_random_read_test.txt
    destroy_fs

    mount_fs
    df >> $DIR/df_before_fio_random_write_test.txt
    pushd $DESTINATION
        fio /tests/$CFG_FILE --section random_write_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_random_write_test.txt
    destroy_fs
}

delete_test() {
    TEST_FILE=$DESTINATION/delete_test_file
    DIR=$OUTPUT_DIRECTORY/delete

	echo "################################################################################"
	echo "### Delete test with trials $DELETION_TEST_TRIALS, output $DIR and gen_size $FILE_SIZE"
	echo "################################################################################"

    mkdir -pv $DIR

    mount_fs
    df >> $DIR/df_before_delete_test.txt
	counter=1
	while [ $counter -le ${DELETION_TEST_TRIALS} ]
        do
            echo "Trial ${counter} / ${DELETION_TEST_TRIALS}"
            genfile --size=$FILE_SIZE --seed=$SEED $TEST_FILE
            rm -fv $TEST_FILE
            ((counter++))
            remount_fs
        done
    df >> $DIR/df_after_delete_test.txt
    destroy_fs
}

append_test() {
    TEST_FILE=$DESTINATION/append_test_file
    DST_FILE=$DESTINATION/destination_test_file
    DIR=$OUTPUT_DIRECTORY/append

	echo "################################################################################"
	echo "### Append test with trials $APPEND_TEST_TRIALS, output $DIR and gen_size $FILE_SIZE"
	echo "################################################################################"

    mkdir -pv $DIR

    mount_fs
    touch $DST_FILE
    df >> $DIR/df_before_append_test.txt
    genfile --size=$FILE_SIZE --seed=$SEED $TEST_FILE
	counter=1
	while [ $counter -le ${APPEND_TEST_TRIALS} ]
        do
            echo "Trial ${counter} / ${APPEND_TEST_TRIALS}"
            cat $TEST_FILE >> $DST_FILE
            ((counter++))
            remount_fs
        done
    rm -rv $TEST_FILE
    rm -rv $DST_FILE
    remount_fs
    df >> $DIR/df_after_append_test.txt
    destroy_fs
}

main() {
    echo "################################################################################"
	echo "################################################################################"
	echo "### PERFORMANCE TEST"
	echo "################################################################################"
	echo "################################################################################"
    echo ""

    mkdir -pv $OUTPUT_DIRECTORY

    for i in $(seq 1 $DELETION_TEST_TRIALS); do
        bonnie_test
    done

    fio_test
    delete_test
    append_test
}

main