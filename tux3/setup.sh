#!/bin/bash

set -euo

KERNEL_DIR=linux
BUILDROOT_DIR=buildroot

function linux() {
	docker build -t tux3-gcc:4.9.4 .
	cp -v .config-linux linux/.config

	cp ./linux-patches/*.patch linux/
	pushd $KERNEL_DIR
		git am *.patch

		docker run \
			--rm \
			-v "$PWD":/usr/src/myapp \
			-w /usr/src/myapp \
			-it tux3-gcc:4.9.4 make -j$(nproc)
	popd
}

function fs_tools() {
    pushd $KERNEL_DIR/fs/tux3
        docker run \
                --rm \
                -v "$PWD":/usr/src/myapp \
                -w /usr/src/myapp \
                -it tux3-gcc:4.9.4 make -C user clean
        docker run \
                --rm \
                -v "$PWD":/usr/src/myapp \
                -w /usr/src/myapp \
                -it tux3-gcc:4.9.4 make -C user
    popd
	mkdir -pv $BUILDROOT_DIR/rootfs-overlay
    cp -R $KERNEL_DIR/fs/tux3/user $BUILDROOT_DIR/rootfs-overlay/
}

function buildroot() {
	unset PERL_MM_OPT
	cp -v ./.config-buildroot $BUILDROOT_DIR/.config
	pushd $BUILDROOT_DIR
		make -j$(nproc)
	popd
}

function main() {
	linux
        fs_tools
	buildroot
}

main
