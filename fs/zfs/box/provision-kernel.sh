#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

export DEBIAN_FRONTEND=noninteractive
KERNEL_SOURCE=/vagrant/linux

# Walkaround for required glibc > 3.34 and clang-15
apt_add_sources() {
	apt-get install -y --allow-unauthenticated gnupg2
	echo 'deb http://ftp.debian.org/debian sid main' >> /etc/apt/sources.list
	sed -r -i 's/^deb(.*)$/deb\1 contrib/g' /etc/apt/sources.list
	echo 'deb http://apt.llvm.org/bullseye/ llvm-toolchain-bullseye-15 main' >> /etc/apt/sources.list
	echo 'deb-src http://apt.llvm.org/bullseye/ llvm-toolchain-bullseye-15 main' >> /etc/apt/sources.list
	wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
	apt-get update
}

install_packages() {
	apt-get \
		-t sid \
		install \
		-y \
		--allow-unauthenticated \
		libc6 libc6-dev libc6-dbg make bc \
		build-essential kmod cpio flex libncurses5-dev libelf-dev libssl-dev dwarves \
		bison wget g++ zlib1g-dev uuid-dev libblkid-dev libblkid1 libmount1 \
		libmount-dev libnvpair3linux libssl-dev virtualbox-guest-x11 \
		virtualbox-guest-utils
	apt-get \
		-t llvm-toolchain-bullseye-15 \
		install \
		-y \
		--allow-unauthenticated \
		libllvm-15-ocaml-dev libllvm15 llvm-15 llvm-15-dev llvm-15-runtime \
		clang-15 lld-15 llvm-15 llvm-15-tools 
}

symlink_llvm_tools() {
	ln /usr/bin/clang-15 /usr/bin/clang
	ln /usr/bin/lld-15 /usr/bin/ld.lld
	ln /usr/bin/llvm-nm-15 /usr/bin/llvm-nm
	ln /usr/bin/llvm-ar-15 /usr/bin/llvm-ar
}

install_kernel_with_modules() {
	pushd $KERNEL_SOURCE
		LLVM=1 make modules_install
		LLVM=1 make install
	popd
}

kernel_from_deb() {
    RELEASE=nilfsdedup-be6be09
	KERNEL_HEADERS=linux-headers-6.1.0-8e25e791a_6.1.0-l_amd64.deb
    KERNEL_IMAGE=linux-image-6.1.0-8e25e791a_6.1.0-l_amd64.deb
	KERNEL_LIBC=linux-libc-dev_6.1.0-l_amd64.deb

	wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_HEADERS
	wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_IMAGE
	wget https://github.com/bachm44/nilfs-dedup/releases/download/$RELEASE/$KERNEL_LIBC

    dpkg -i $KERNEL_HEADERS
    dpkg -i $KERNEL_IMAGE
    dpkg -i $KERNEL_LIBC
}

main() {
	apt_add_sources
	install_packages
	symlink_llvm_tools
	# install_kernel_with_modules
	kernel_from_deb
}

main