#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
cd /vagrant
sudo bash setup.sh
sudo bash test_template.sh COPYFS
sudo bash teardown.sh
HEREDOC

vagrant destroy -f