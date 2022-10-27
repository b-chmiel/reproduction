#!/bin/bash

set -euo

function packages {
    apt-get update && \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y wget make g++ libfuse-dev

    wget -O - http://cpanmin.us | perl - --self-upgrade
    sudo cpanm install Algorithm::Diff
}

function bonnie {
    BONNIE_VERSION=2.00b

    wget https://github.com/bachm44/bonnie-plus-plus/archive/refs/tags/$BONNIE_VERSION.tar.gz
    mkdir -pv ./bonnie
    tar -xf *.tar.gz -C ./bonnie --strip-components=1
    cd bonnie
    make install
}

function install_fs {
    cp -rv /vagrant/source/ /home/vagrant/
    cd /home/vagrant/source
    ./configure
    make all
    make install
}

function main {
    packages
    bonnie
    install_fs
}

main

