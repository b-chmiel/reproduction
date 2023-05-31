#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

apt_packages() {
    apt-get update && \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y --allow-unauthenticated wget make g++ btrfs-progs duperemove \
            git pkg-config build-essential btrfs-progs libbtrfs-dev uuid-dev markdown \
            uuid-runtime python3-pip libsqlite3-dev
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
        make -j2
        make install
    popd
}

genfile_install() {
    GENFILE_VERSION=1.0.5-dev-09dfc220ea449a02f71f59dfd803e676a2db7905
    GENFILE=genfile.deb

    wget https://github.com/bachm44/genfile/releases/download/$GENFILE_VERSION/genfile.deb
    dpkg -i $GENFILE
}

kernel_install() {
    RELEASE=nilfsdedup-f08aabf
    KERNEL_IMAGE=linux-image-6.1.0-32b0e7d60_6.1.0-l_amd64.deb
    KERNEL_HEADERS=linux-headers-6.1.0-32b0e7d60_6.1.0-l_amd64.deb
    KERNEL_LIBC=linux-libc-dev_6.1.0-l_amd64.deb

    wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_IMAGE
    wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_HEADERS
    wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_LIBC

    dpkg -i $KERNEL_IMAGE
    dpkg -i $KERNEL_HEADERS
    dpkg -i $KERNEL_LIBC
}

bees_install() {
    DIR=./bees

    git clone --branch v0.9.3 --depth 1 https://github.com/Zygo/bees.git

    pushd $DIR
        make -j2
        make install
    popd
}

dduper_install() {
    DIR=./dduper
    COMMIT=11b78558f1b1677ce9407909cecaeb3374828adb
    git clone https://github.com/Lakshmipathi/dduper.git

    pushd $DIR
        git checkout $COMMIT
        pip install -r requirements.txt
        cp -v bin/btrfs.static /usr/sbin/
        cp -v dduper /usr/sbin/        
    popd
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
    genfile_install
    kernel_install
    bees_install
    dduper_install
    fix_keys
}

main