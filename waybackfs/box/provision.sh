#!/bin/bash

set -euo


function packages() {
    apt-get update && \
	export DEBIAN_FRONTEND=noninteractive && \
	apt-get install -y wget make g++ gcc libfuse-dev fuse pkg-config
}

function bonnie {
    BONNIE_VERSION=2.00b

    wget https://github.com/bachm44/bonnie-plus-plus/archive/refs/tags/$BONNIE_VERSION.tar.gz
    mkdir -pv ./bonnie
    tar -xf *.tar.gz -C ./bonnie --strip-components=1
    cd bonnie
    make install
}

function wayback() {
    pushd /vagrant/source
	make
	make install
    popd
}

function fix_ssh_keys() {
    wget --no-check-certificate https://raw.github.com/mitchellh/vagrant/master/keys/vagrant.pub -O /home/vagrant/.ssh/authorized_keys  
    chmod 0700 /home/vagrant/.ssh  
    chmod 0600 /home/vagrant/.ssh/authorized_keys  
    chown -R vagrant /home/vagrant/.ssh  
}

function main() {
    packages
    bonnie
    wayback
    fix_ssh_keys
}

main

