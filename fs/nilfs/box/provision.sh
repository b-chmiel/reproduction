#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

apt_packages() {
    apt-get update && \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y --allow-unauthenticated nilfs-tools wget make g++
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

gen_file_install() {
    GEN_FILE_VERSION=1.0.5-dev-aa8ab56514bd6b4bf7ac5669b620c53b604fcf82
    DIR=./gen_file_install

    wget https://github.com/bachm44/gen_file/releases/download/$GEN_FILE_VERSION/gen_file-$GEN_FILE_VERSION.tar.gz
    mkdir -pv $DIR
    tar -xf *.tar.gz -C $DIR --strip-components=1
    rm *.tar.gz
    pushd $DIR
        ./configure
        make
        make install
    popd
}

kernel_install() {
    KERNEL_VERSION=dat-dedup-a55606
    KERNEL_IMAGE=linux-image-6.1.0-35fa9482ae36044c4267b4b4fae7523ce3929a2a_6.1.0-l_amd64.deb
    wget https://github.com/bachm44/nilfs-dedup/releases/download/$KERNEL_VERSION/$KERNEL_IMAGE
    dpkg -i $KERNEL_IMAGE
}

fix_keys() {
    wget --no-check-certificate https://raw.github.com/mitchellh/vagrant/master/keys/vagrant.pub -O /home/vagrant/.ssh/authorized_keys  
    chmod 0700 /home/vagrant/.ssh  
    chmod 0600 /home/vagrant/.ssh/authorized_keys  
    chown -R vagrant /home/vagrant/.ssh  
}

main() {
    apt_packages
    bonnie
    fio_install
    gen_file_install
    kernel_install
    fix_keys
}

main