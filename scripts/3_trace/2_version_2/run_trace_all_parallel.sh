#!/bin/bash

#OPTIONS
log_dir="./traces-10m"
corpus_root="./corpora-10m"
base_port="8700"
DATA_FILE="./04_to_trace.txt"
# DATA_FILE="projects_fuzzers_UNfinished.txt"
#OPTIONS

rm -rf $log_dir
docker ps --filter name="reproduce_.*" -q | xargs docker rm -f
# bash docker_clean.sh

mkdir -p $log_dir
mkdir -p $log_dir/logs-exe
mkdir -p $log_dir/logs-tracer
mkdir -p $log_dir/logs-worker
mkdir -p $log_dir/logs-xmls

num_workers=8
echo Starting $num_workers workers at $(date)...

parallel --progress --group -N 2 -j$num_workers bash $(dirname $0)/run_trace_all_worker.sh $log_dir $base_port "{%}" $corpus_root {} ::: $(cat $DATA_FILE) > $log_dir/trace_all.log
# bash $(dirname $0)/run_trace_all_worker.sh $log_dir $base_port "1" $corpus_root $(head -n1 $DATA_FILE) > $log_dir/trace_all.log

trap "exit" INT TERM
trap "kill 0" EXIT
wait < <(jobs -p)

echo Done at $(date)...
