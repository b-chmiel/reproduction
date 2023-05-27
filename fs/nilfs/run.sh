#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
set -euo pipefail
IFS=$'\n\t'

sudo bash /vagrant/setup.sh
sudo bash /tests/test.sh NILFS2
sudo bash /vagrant/teardown.sh
HEREDOC

vagrant destroy -f