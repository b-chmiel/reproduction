#!/bin/bash

set -euo

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
cd /vagrant
sudo bash setup.sh
sudo bash test_template.sh WAYBACKFS
sudo bash teardown.sh
HEREDOC

vagrant destroy -f