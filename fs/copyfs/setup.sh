#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source test_template_env.sh

mkdir -pv /home/vagrant/versions
mkdir -pv $DESTINATION
copyfs-mount /home/vagrant/versions $DESTINATION