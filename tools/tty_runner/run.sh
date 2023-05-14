#!/bin/bash

set -euo pipefail

./build/src/tty --path-to-makefile ../../fs/nilfs-dedup --command-list commands/generate.sh --output-file tty_output_generate.log

./build/src/tty --path-to-makefile ../../fs/nilfs-dedup --command-list commands/dedup.sh --output-file tty_output_dedup.log

./build/src/tty --path-to-makefile ../../fs/nilfs-dedup --command-list commands/validate.sh --output-file tty_output_validate.log

