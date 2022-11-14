#!/bin/bash

set -euo

vagrant destroy -f && vagrant up

vagrant ssh -- -t <<HEREDOC
cd /vagrant
sudo bash test.sh
HEREDOC

vagrant destroy -f