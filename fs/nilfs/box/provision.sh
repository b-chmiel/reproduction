#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

CACHE_DIR=/vagrant/.cache

apt_packages() {
    apt-get update && \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y --allow-unauthenticated nilfs-tools wget make g++
}

bonnie_install() {
    BONNIE_VERSION=2.00b
    DIR=$CACHE_DIR/bonnie_install

    if [ ! -d $DIR ]
    then
        wget https://github.com/bachm44/bonnie-plus-plus/archive/refs/tags/$BONNIE_VERSION.tar.gz
        mkdir -pv $DIR
        tar -xf *.tar.gz -C $DIR --strip-components=1
        rm *.tar.gz
    fi

    pushd $DIR
        make install
    popd
}

fio_install() {
    FIO_VERSION=fio-3.33
    DIR=$CACHE_DIR/fio_install

    if [ ! -d $DIR ]
    then
        wget https://github.com/axboe/fio/archive/refs/tags/$FIO_VERSION.tar.gz
        mkdir -pv $DIR
        tar -xf *.tar.gz -C $DIR --strip-components=1
        rm *.tar.gz
    fi

    pushd $DIR
        ./configure
        make
        make install
    popd
}

gen_file_install() {
    GEN_FILE_VERSION=1.0.5-dev-aa8ab56514bd6b4bf7ac5669b620c53b604fcf82
    DIR=$CACHE_DIR/gen_file_install

    if [ ! -d $DIR ]
    then
        wget https://github.com/bachm44/gen_file/releases/download/$GEN_FILE_VERSION/gen_file-$GEN_FILE_VERSION.tar.gz
        mkdir -pv $DIR
        tar -xf *.tar.gz -C $DIR --strip-components=1
        rm *.tar.gz
    fi

    pushd $DIR
        ./configure
        make
        make install
    popd
}

kernel_install() {
    RELEASE=nilfsdedup-f08aabf
    KERNEL_IMAGE=linux-image-6.1.0-32b0e7d60_6.1.0-l_amd64.deb
    KERNEL_HEADERS=linux-headers-6.1.0-32b0e7d60_6.1.0-l_amd64.deb
    KERNEL_LIBC=linux-libc-dev_6.1.0-l_amd64.deb

    DIR=$CACHE_DIR/linux_install

    if [ ! -d $DIR]
    then
        mkdir -pv $DIR
    fi

    if [ ! -f $DIR/$KERNEL_IMAGE ]
    then
        wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_IMAGE
        mv -v $KERNEL_IMAGE $DIR/$KERNEL_IMAGE
    fi

    if [ ! -f $DIR/$KERNEL_HEADERS ]
    then
        wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_HEADERS
        mv -v $KERNEL_HEADERS $DIR/$KERNEL_HEADERS
    fi

    if [ ! -f $DIR/$KERNEL_LIBC ]
    then
        wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_LIBC
        mv -v $KERNEL_LIBC $DIR/$KERNEL_LIBC
    fi

    dpkg -i $DIR/$KERNEL_IMAGE
    dpkg -i $DIR/$KERNEL_HEADERS
    dpkg -i $DIR/$KERNEL_LIBC
}

fix_keys() {
    wget --no-check-certificate https://raw.github.com/mitchellh/vagrant/master/keys/vagrant.pub -O /home/vagrant/.ssh/authorized_keys  
    chmod 0700 /home/vagrant/.ssh  
    chmod 0600 /home/vagrant/.ssh/authorized_keys  
    chown -R vagrant /home/vagrant/.ssh  
}

main() {
    apt_packages
    bonnie_install
    fio_install
    gen_file_install
    kernel_install
    fix_keys
}

main