#!/bin/bash

set -euo pipefail

NILFS_DEDUP_PATH=../../fs/nilfs-dedup

./build/src/tty \
	--path-to-makefile $NILFS_DEDUP_PATH \
	--command-list-setup commands/setup.sh \
	--command-list commands/generate.sh \
	--output-file tty_output_generate.log \
	--show-output 1

./build/src/tty \
	--path-to-makefile ../../fs/nilfs-dedup \
	--command-list-setup commands/setup.sh \
	--command-list commands/dedup.sh \
	--output-file tty_output_dedup.log \
	--show-output 1

./build/src/tty \
	--path-to-makefile ../../fs/nilfs-dedup \
	--command-list-setup commands/setup.sh \
	--command-list commands/validate.sh \
	--output-file tty_output_validate.log \
	--show-output 1

# since output files are saved by process run as root, this is required
sudo chown incvis:incvis -R $NILFS_DEDUP_PATH/out/
