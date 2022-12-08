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

	cp -v templates/\#test_template.sh fs/$fs_name/test_template.sh | adddate
	cp -v templates/\#test_template_env.sh fs/$fs_name/test_template_env.sh | adddate
	cp -v templates/\#fio-job.cfg fs/$fs_name/fio-job.cfg | adddate

	pushd fs/$fs_name
		bash run.sh | adddate
	popd
}

export -f benchmark

copy_fio_logs() {
	fs_name=$@
	log "Copy logs for ${fs_name}"
	mkdir -pv build/fio/logs

	pushd fs/$fs_name/out/fio
		for i in *.log ; do cp $i "../../../../build/fio/logs/${fs_name}_${i}" ; done
	popd
}

export -f copy_fio_logs

generate_gnuplot() {
	fio_test=$@
	log "Generate gnuplot for ${fio_test}"
	pushd build/fio/logs
		rm -rfv ../gnuplot/$fio_test
		mkdir -pv ../gnuplot/$fio_test
		fio2gnuplot -t $fio_test -d ../gnuplot/$fio_test -p "*${fio_test}_bw*.log" -v
	popd
}

export -f generate_gnuplot

main() {
	file_systems=('copyfs' 'ext4' 'nilfs' 'waybackfs')
	fio_tests=('file_append_read_test' 'file_append_write_test' 'random_read_test' 'random_write_test')

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