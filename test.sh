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

copy_fio_logs() {
	fs_name=$@
	log "Copy logs for ${fs_name}"
	mkdir -pv output/fio/logs

	pushd fs/$fs_name/out/fio
		for i in *.log ; do cp $i "../../../../output/fio/logs/${fs_name}_${i}" ; done
	popd
}

export -f copy_fio_logs

generate_gnuplot() {
	fio_test=$@
	log "Generate gnuplot for ${fio_test}"
	pushd output/fio/logs
		rm -rfv ../gnuplot/$fio_test
		mkdir -pv ../gnuplot/$fio_test
		fio2gnuplot -t $fio_test -d ../gnuplot/$fio_test -p "*${fio_test}_bw*.log" -v
	popd
}

export -f generate_gnuplot

main() {
	file_systems=('btrfs' 'copyfs' 'nilfs' 'nilfs-dedup' 'waybackfs')
	fio_tests=('random_read_test' 'random_write_test' 'append_read_test' 'append_write_test')

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

	log "Copy fio logs"
	parallel \
		--results ${LOG_DIR}/copy-results \
		--joblog ${LOG_DIR}/copy.log \
		-j8 \
		--tag \
		--line-buffer \
		--halt-on-error now,fail=1 \
		copy_fio_logs ::: ${file_systems[@]}

	log "Generate gnuplot rendering scripts for fio tests: ${fio_tests[*]}"
	parallel \
		--results ${LOG_DIR}/gnuplot-results \
		--joblog ${LOG_DIR}/gnuplot.log \
		-j8 \
		--tag \
		--line-buffer \
		--halt-on-error now,fail=1 \
		generate_gnuplot ::: ${fio_tests[@]}

	log "Generate graphs"
	python graphs.py | adddate

	log "Finished successfully"
}

main
exit 0