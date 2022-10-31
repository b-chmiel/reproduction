#!/bin/bash

set -euo

function buildroot() {
	make -C buildroot clean
	rm -rf buildroot/rootfs-overlay
}

function linux() {
	make -C linux clean
	make -C linux/fs/tux3/user clean
	pushd linux
		git restore .
	popd
}

function main() {
	buildroot
	linux
}

main