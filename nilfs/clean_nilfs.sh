#!/bin/sh

# cleans all snapshots
nilfs-clean -p 1s /mnt /dev/loop0
