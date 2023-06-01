#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
set -euo pipefail
IFS=$'\n\t'

sudo bash /tests/test.sh BTRFS
sudo bash /tests/test_btrfs_dedup.sh
HEREDOC

vagrant destroy -f