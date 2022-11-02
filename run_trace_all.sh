#!/bin/bash

log_dir="traces-1m"

rm -rf trace_all_*.log $log_dir

mkdir -p $log_dir
mkdir -p $log_dir/logs-exe
mkdir -p $log_dir/logs-tracer

while read p
do
    while read f
    do
        echo running $p $f... >> trace_all_exe.log
        PROJECT_NAME="$p"
        FUZZER="$f"
        SAN="address"
        ARCH="x86_64"
        corpus_dir="corpora-1m/$PROJECT_NAME/$SAN-$ARCH-$FUZZER"
        id="$PROJECT_NAME-$FUZZER"
        exe_log="$log_dir/logs-exe/$id.log"
        tracer_log="$log_dir/logs-tracer/$id.log"

        bash tracing_2_exe.sh $PROJECT_NAME $FUZZER $corpus_dir &> $exe_log &
        P1=$!
        
        sleep 3s
        should_trace=true
        while ! grep -q "Listening for transport dt_socket at address: 8787" $exe_log
        do
            sleep 1s
            if [ ! -e /proc/$P1 ]
            then
                echo Process $P1 for $p-$f quit. Skipping. >&2
                should_trace=false
                break
            fi
            echo Waiting on $P1 $exe_log for listener... >&2
        done
        if [ "$should_trace" = true ]
        then
            (timeout 10m bash tracing_2_tracer.sh) &> $tracer_log &
            P2=$!
            wait $P1 $P2
        fi
        echo Traced $p-$f
    done < projects/$p/fuzzers.txt
done < java-projects-from-csv.txt | tqdm --total $(cat projects/*/fuzzers.txt | wc -l) >> /dev/null
