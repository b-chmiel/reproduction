#!/bin/bash

set -euo pipefail

WORKSPACE=${WORKSPACE:-$(pwd)}
LOG_DIR=${LOG_DIR:-$(pwd)/logs/build_boxes}

log() { 
	echo "[$(date +"%F %T")] $@"; 
}

export -f log

build_box() {
	 fs_name=$@

	 log "Building box for ${fs_name}"

	box="reproduction-${fs_name}"	
	box_file="${box}.box"

	cd $fs_name/box && \
		vagrant destroy -f && \
		rm -vf $box_file && \
		vagrant up && \
		vagrant package --base $box --output $box_file && \
		vagrant destroy -f && \
		vagrant box remove $box -f || true && \
		vagrant box add $box $box_file && \
		rm -vf $box_file
}

export -f build_box

main() {
	file_systems=('copyfs' 'ext4' 'nilfs' 'waybackfs')

	log "Building vagrant base boxes for: ${file_systems[*]}"

	mkdir -pv $LOG_DIR

	parallel \
		--results ${LOG_DIR}/results \
		--joblog ${LOG_DIR}/job.log \
		-j8 \
		--tag \
		--line-buffer \
		build_box {1} ::: ${file_systems[@]}
	
	log "Finished successfully"
}

main 
exit 0