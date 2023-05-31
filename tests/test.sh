#!/bin/bash

set -euo pipefail

if [[ $# -eq 0 ]] ; then
    echo 'Test template need fs_name argument'
    exit 1
fi

FS_NAME=$1

source /tests/test_env.sh

bonnie_test() {
    DIR=$OUTPUT_DIRECTORY/bonnie

	echo "################################################################################"
	echo "### Bonnie++ test for args $BONNIE_ARGS and output directory $DIR"
	echo "################################################################################"

    mkdir -pv $DIR

    df >> $DIR/df_before_bonnie.txt
    bonnie++ $BONNIE_ARGS -m $FS_NAME >> $DIR/out.csv
    df >> $DIR/df_after_bonnie.txt
}

fio_test() {
    DIR=$OUTPUT_DIRECTORY/fio
    CFG_FILE=fio-job.cfg

	echo "################################################################################"
	echo "### Fio test for cfg file $CFG_FILE, output directory $DIR"
	echo "################################################################################"

    mkdir -pv $DIR

    cp -v /tests/fio-job.cfg $DESTINATION/
    pushd $DESTINATION
        df >> $DIR/df_before_fio_file_append_read_test.txt
        fio $CFG_FILE --section file_append_read_test
        df >> $DIR/df_after_fio_file_append_read_test.txt

        df >> $DIR/df_before_fio_file_append_write_test.txt
        fio $CFG_FILE --section file_append_write_test
        df >> $DIR/df_after_fio_file_append_write_test.txt

        df >> $DIR/df_before_fio_random_read_test.txt
        fio $CFG_FILE --section random_read_test
        df >> $DIR/df_after_fio_random_read_test.txt

        df >> $DIR/df_before_fio_random_write_test.txt
        fio $CFG_FILE --section random_write_test
        df >> $DIR/df_after_fio_random_write_test.txt

        mv *.log $DIR/
    popd
}

delete_test() {
    TRIALS=2
    TEST_FILE=delete_test_file
    GEN_SIZE=1G
    DIR=$OUTPUT_DIRECTORY/delete

	echo "################################################################################"
	echo "### Delete test with trials $TRIALS, output $DIR and gen_size $GEN_SIZE"
	echo "################################################################################"

    mkdir -pv $DIR

    df >> $DIR/df_before_delete_test.txt
    pushd $DESTINATION
	counter=1
	while [ $counter -le ${TRIALS} ]
        do
	    echo "Trial ${counter} / ${TRIALS}"
	
            genfile --size=$GEN_SIZE --seed=$SEED $TEST_FILE
            rm -fv $TEST_FILE
	    ((counter++))
        done
    popd
    df >> $DIR/df_after_delete_test.txt
}

main() {
    echo "################################################################################"
	echo "################################################################################"
	echo "### PERFORMANCE TEST"
	echo "################################################################################"
	echo "################################################################################"
    echo ""

    mkdir -pv $OUTPUT_DIRECTORY

    bonnie_test
    fio_test
    delete_test
}

main