#!/bin/bash

set -euo

apt_packages() {
    apt-get update && \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y nilfs-tools wget make g++
}

bonnie() {
    BONNIE_VERSION=2.00b
    DIR=./bonnie_install

    wget https://github.com/bachm44/bonnie-plus-plus/archive/refs/tags/$BONNIE_VERSION.tar.gz
    mkdir -pv $DIR
    tar -xf *.tar.gz -C $DIR --strip-components=1
    rm *.tar.gz
    pushd $DIR
        make install
    popd
}

fio_install() {
    FIO_VERSION=fio-3.33
    DIR=./fio_install

    wget https://github.com/axboe/fio/archive/refs/tags/$FIO_VERSION.tar.gz
    mkdir -pv $DIR
    tar -xf *.tar.gz -C $DIR --strip-components=1
    rm *.tar.gz
    pushd $DIR
        ./configure
        make
        make install
    popd
}

fix_ssh_keys() {
    wget --no-check-certificate https://raw.github.com/mitchellh/vagrant/master/keys/vagrant.pub -O /home/vagrant/.ssh/authorized_keys  
    chmod 0700 /home/vagrant/.ssh  
    chmod 0600 /home/vagrant/.ssh/authorized_keys  
    chown -R vagrant /home/vagrant/.ssh  
}

main() {
    apt_packages
    bonnie
    fio_install
    fix_ssh_keys
}

main