#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<EOF
set -euo pipefail
IFS=$'\n\t'

sudo bash /vagrant/setup.sh
sudo bash /tests/test.sh COPYFS
sudo bash /vagrant/teardown.sh
EOF

vagrant destroy -f
