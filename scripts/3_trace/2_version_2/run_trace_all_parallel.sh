#!/bin/bash

#OPTIONS
log_dir="traces-1m-worker"
quit_after_one=false
base_port="8700"
#OPTIONS

rm -rf $log_dir
# bash docker_clean.sh

mkdir -p $log_dir
mkdir -p $log_dir/logs-exe
mkdir -p $log_dir/logs-tracer
mkdir -p $log_dir/logs-worker

num_workers=8
echo Starting $num_workers workers at $(date)...

for i in $(seq 0 $(( num_workers - 1 )))
do
    bash $(dirname $0)/run_trace_all_worker.sh $log_dir $(( $base_port + $i )) $num_workers $i &> $log_dir/logs-worker/worker_$i.log &
done

trap "exit" INT TERM
trap "kill 0" EXIT
wait < <(jobs -p)

echo Done at $(date)...
