#!/bin/bash

#OPTIONS
log_dir="traces-10m"
corpus_root="fuzz_run_5_complete/corpora-10m"
base_port="8700"
DATA_FILE="data/1_preprocess/java-projects-fuzzers-from-csv-fixed.txt"
# DATA_FILE="projects_fuzzers_UNfinished.txt"
#OPTIONS

rm -rf $log_dir
# bash docker_clean.sh

mkdir -p $log_dir
mkdir -p $log_dir/logs-exe
mkdir -p $log_dir/logs-tracer
mkdir -p $log_dir/logs-worker
mkdir -p $log_dir/logs-xmls

num_workers=8
echo Starting $num_workers workers at $(date)...

parallel --progress --group -N 2 -j$num_workers bash $(dirname $0)/run_trace_all_worker.sh $log_dir $base_port "{%}" $corpus_root {} ::: $(cat $DATA_FILE) > $log_dir/trace_all.log

trap "exit" INT TERM
trap "kill 0" EXIT
wait < <(jobs -p)

echo Done at $(date)...
