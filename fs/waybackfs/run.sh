#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
set -euo pipefail
IFS=$'\n\t'

sudo bash /tests/test.sh WAYBACKFS
HEREDOC

vagrant destroy -f