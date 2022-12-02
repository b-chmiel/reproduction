#!/bin/bash

# This file will be copied to each folder with file system
# and executed in Vagrantbox

set -euo pipefail

if [[ $# -eq 0 ]] ; then
    echo 'Test template need fs_name argument'
    exit 1
fi

FS_NAME=$1

source test_template_env.sh

bonnie_test() {
    DIR=$OUTPUT_DIRECTORY/bonnie
    mkdir -pv $DIR

    echo "Running bonnie++ benchmark..."

    df >> $DIR/df_before_bonnie.txt
    bonnie++ $BONNIE_ARGS -m $FS_NAME >> $DIR/out.csv
    df >> $DIR/df_after_bonnie.txt
}

fio_test() {
    DIR=$OUTPUT_DIRECTORY/fio
    mkdir -pv $DIR

    mv fio-job.cfg $DESTINATION/
    pushd $DESTINATION
        df >> $DIR/df_before_fio_file_append_read_test.txt
        fio fio-job.cfg --section file_append_read_test
        df >> $DIR/df_after_fio_file_append_read_test.txt

        df >> $DIR/df_before_fio_file_append_write_test.txt
        fio fio-job.cfg --section file_append_write_test
        df >> $DIR/df_after_fio_file_append_write_test.txt

        df >> $DIR/df_before_fio_random_read_test.txt
        fio fio-job.cfg --section random_read_test
        df >> $DIR/df_after_fio_random_read_test.txt

        df >> $DIR/df_before_fio_random_write_test.txt
        fio fio-job.cfg --section random_write_test
        df >> $DIR/df_after_fio_random_write_test.txt

        mv *.log $DIR/
    popd
}

delete_test() {
    TRIALS=5
    TEST_FILE=delete_test_file
    DIR=$OUTPUT_DIRECTORY/delete
    mkdir -pv $DIR

    echo "Running deletion test for: ${TRIALS} trials"

    df >> $DIR/df_before_delete_test.txt
    pushd $DESTINATION
        for i in {1..$TRIALS}
        do
        	echo "Trial ${i} / ${TRIALS}"
            gen_file --size=$TEST_FILE --seed=420 $TEST_FILE
            rm $TEST_FILE
        done
    popd
    df >> $DIR/df_after_delete_test.txt
}

main() {
    mkdir -pv $OUTPUT_DIRECTORY

    bonnie_test
    fio_test
    delete_test
}

main