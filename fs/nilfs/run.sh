#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
set -euo pipefail
IFS=$'\n\t'

cd /vagrant
sudo bash setup.sh
sudo bash test_template.sh NILFS2
sudo bash teardown.sh
HEREDOC

vagrant destroy -f