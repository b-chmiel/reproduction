#!/bin/bash

set -euo pipefail

function build_box() {
	fs_name=$1

	echo $fs_name
	# cd $fs_name/box && \
	# vagrant destroy -f && \
	# rm -vf reproduction-$fs_name.box && \
	# vagrant up && \
	# vagrant package --base reproduction-$fs_name --output reproduction-<replace>.box && \
	# vagrant destroy -f && \
	# vagrant box remove reproduction-$fs_name -f || true && \
	# vagrant box add reproduction-$fs_name reproduction-<replace>.box && \
	# rm -vf reproduction-$fs_name.box
}

function main() {
	parallel --tmuxpane --fg build_box ::: btrfs copyfs ext4 nilfs waybackfs
}

main