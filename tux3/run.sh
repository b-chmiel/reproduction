#!/bin/bash

set -euo

KERNEL_DIR=linux-tux3
BUILDROOT_DIR=buildroot

function buildroot() {
	unset PERL_MM_OPT
	cp ./.config-buildroot $BUILDROOT_DIR/.config
	pushd $BUILDROOT_DIR
		make -j$(nproc)
	popd
}

function linux() {
	docker build -t tux3-gcc:4.9.4 .

	pushd linux-tux3
		docker run \
			--rm \
			-v "$PWD":/usr/src/myapp \
			-w /usr/src/myapp \
			-it tux3-gcc:4.9.4 make -j$(nproc)
	popd
}

function qemu() {
	qemu-system-x86_64 \
		-kernel $KERNEL_DIR/arch/x86/boot/bzImage \
		-boot c \
		-m 2049M \
		-hda $BUILDROOT_DIR/output/images/rootfs.ext2 \
		-append "root=/dev/sda rw console=ttyS0,115200 acpi=off nokaslr" \
		-serial stdio \
		-display none \
		-enable-kvm \
		-virtfs local,path=$(pwd),mount_tag=host0,security_model=mapped,id=host0
}

function main() {
	buildroot
	linux
	qemu
}

main
