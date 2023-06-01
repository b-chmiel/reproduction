#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source /tests/test_env.sh

umount_fs() {
echo 'Umounting fs'
busy=true
while $busy
do
 if mountpoint -q $DESTINATION
 then
  exit_code=$?
  if umount -rv $DESTINATION ; then
   busy=false  # umount successful
  else
  sync
   echo '.'  # output to show that the script is alive
   sleep 5      # 5 seconds for testing, modify to 300 seconds later on
  fi
 else
  busy=false  # not mounted
 fi
done
echo "Unmounted successfully"
}

mount_fs() {
	fallocate --verbose -l $FILESYSTEM_FILE_SIZE $FILESYSTEM_FILE
	mkfs -t nilfs2 $FILESYSTEM_FILE
	mkdir -pv $DESTINATION
	mount -i -v -t nilfs2 $FILESYSTEM_FILE $DESTINATION
}

remount_fs() {
	umount_fs
	mount -i -v -t nilfs2 $FILESYSTEM_FILE $DESTINATION
}

destroy_fs() {
	umount_fs || true
	rm -fv $FILESYSTEM_FILE
	sync
}