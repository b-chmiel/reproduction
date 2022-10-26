#!/bin/sh

set -euo

apt-get update && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y nilfs-tools wget make g++


BONNIE_VERSION=2.00b

wget https://github.com/bachm44/bonnie-plus-plus/archive/refs/tags/$BONNIE_VERSION.tar.gz
mkdir -pv ./bonnie
tar -xf *.tar.gz -C ./bonnie --strip-components=1
cd bonnie
make install
