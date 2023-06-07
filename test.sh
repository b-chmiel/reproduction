#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

WORKSPACE=${WORKSPACE:-$(pwd)}
LOG_DIR=${LOG_DIR:-$(pwd)/logs/test}

log() { 
	echo "[$(date +"%F %T")] $@"; 
}

export -f log

# https://serverfault.com/a/310104
adddate() {
    while IFS= read -r line; do
		log "==> ${line}"
    done
}

export -f adddate

benchmark() { 
	fs_name=$@
	log "Running benchmark for ${fs_name}"

	pushd fs/$fs_name
		bash run.sh | adddate
	popd
}

export -f benchmark

main() {
	file_systems=('btrfs' 'copyfs' 'nilfs' 'nilfs-dedup' 'waybackfs')

	mkdir -pv $LOG_DIR

	log "Benchmarking file systems: ${file_systems[*]}"
	parallel \
		--results ${LOG_DIR}/benchmark-results \
		--joblog ${LOG_DIR}/benchmark.log \
		-j8 \
		--tag \
		--line-buffer \
		--halt-on-error now,fail=1 \
		benchmark ::: ${file_systems[@]}

	log "Generate graphs"
	python graphs.py | adddate

	log "Finished successfully"
}

main
exit 0