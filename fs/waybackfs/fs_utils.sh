#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source /tests/test_env.sh

SOURCE_DIR=/source
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
	mkdir -pv $SOURCE_DIR
	mkdir -pv $DESTINATION
	wayback -- $SOURCE_DIR $DESTINATION
}

remount_fs() {
	umount_fs
	wayback -- $SOURCE_DIR $DESTINATION
}

destroy_fs() {
	umount_fs || true
	rm -rf $SOURCE_DIR
	rm -rf $DESTINATION
	sync
}