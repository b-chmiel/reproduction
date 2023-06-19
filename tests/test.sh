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
    CFG_FILE=/tests/fio-job.cfg

	echo "################################################################################"
	echo "### Fio test for cfg file $CFG_FILE, output directory $DIR"
	echo "################################################################################"

    mkdir -pv $DIR

    mount_fs
    df >> $DIR/df_before_fio_random_read_test.txt
    pushd $DESTINATION
        fio $CFG_FILE --section random_read_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_random_read_test.txt
    destroy_fs

    mount_fs
    df >> $DIR/df_before_fio_random_write_test.txt
    pushd $DESTINATION
        fio $CFG_FILE --section random_write_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_random_write_test.txt
    destroy_fs

    mount_fs
    df >> $DIR/df_before_fio_sequential_read_test.txt
    pushd $DESTINATION
        fio $CFG_FILE --section sequential_read_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_sequential_read_test.txt
    destroy_fs

    mount_fs
    df >> $DIR/df_before_fio_sequential_write_test.txt
    pushd $DESTINATION
        fio $CFG_FILE --section sequential_write_test
        mv *.log $DIR/
    popd
    remount_fs
    df >> $DIR/df_after_fio_sequential_write_test.txt
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

    for i in $(seq 1 $BONNIE_RUNS); do
        bonnie_test
    done

    fio_test

    echo "################################################################################"
	echo "################################################################################"
	echo "### FINISHED PERFORMANCE TEST"
	echo "################################################################################"
	echo "################################################################################"
    echo ""
}

main