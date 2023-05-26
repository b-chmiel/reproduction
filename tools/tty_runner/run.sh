#!/bin/bash

set -euo pipefail

NILFS_DEDUP_PATH=../../fs/nilfs-dedup

./build/src/tty \
	--path-to-makefile $NILFS_DEDUP_PATH \
	--command-list-setup tmp/setup.sh \
	--command-list tmp/generate.sh \
	--output-file tty_output_generate.log \
	--verbosity 8

./build/src/tty \
	--path-to-makefile ../../fs/nilfs-dedup \
	--command-list-setup tmp/setup.sh \
	--command-list tmp/dedup.sh \
	--output-file tty_output_dedup.log \
	--verbosity 8

./build/src/tty \
	--path-to-makefile ../../fs/nilfs-dedup \
	--command-list-setup tmp/setup.sh \
	--command-list tmp/validate.sh \
	--output-file tty_output_validate.log \
	--verbosity 8

# since output files are saved by process run as root, this is required
sudo chown incvis:incvis -R $NILFS_DEDUP_PATH/out/
