#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

export DEBIAN_FRONTEND=noninteractive

apt_packages() {
	sed -r -i 's/^deb(.*)$/deb\1 contrib/g' /etc/apt/sources.list 
    apt-get update
    apt-get install -y --allow-unauthenticated \
        wget make g++ uuid-dev libblkid-dev libblkid1 libmount1 libmount-dev \
        dpkg-dev linux-headers-generic linux-image-generic zfs-dkms zfsutils-linux
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
    fix_keys
}

main