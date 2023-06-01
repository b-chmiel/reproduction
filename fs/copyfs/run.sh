#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<EOF
set -euo pipefail
IFS=$'\n\t'

sudo bash /tests/test.sh COPYFS
EOF

vagrant destroy -f
