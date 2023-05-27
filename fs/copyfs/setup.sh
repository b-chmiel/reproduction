#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source /tests/test_env.sh

mkdir -pv /home/vagrant/versions
mkdir -pv $DESTINATION
copyfs-mount /home/vagrant/versions $DESTINATION