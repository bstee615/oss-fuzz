#!/bin/bash

#OPTIONS
quit_after_one=false

log_dir="$1"
port="$2"
num_workers="$3"
worker_id="$4"
#OPTIONS

data_file="$log_dir/logs-worker/worker_${worker_id}_work.txt"
python3 splitsville.py failed-projects.txt $num_workers $worker_id > $data_file

while read l
do
    p=$(echo $l | cut -d' ' -f1)
    f=$(echo $l | cut -d' ' -f2)
    # echo running $p $f... 1>&2

    PROJECT_NAME="$p"
    FUZZER="$f"
    SAN="address"
    ARCH="x86_64"
    corpus_dir="corpora-1m/$PROJECT_NAME/$SAN-$ARCH-$FUZZER"
    id="$PROJECT_NAME-$FUZZER"
    exe_log="$log_dir/logs-exe/$id.log"
    tracer_log="$log_dir/logs-tracer/$id.log"

    bash tracing_2_exe.sh $PROJECT_NAME $FUZZER $corpus_dir $port &> $exe_log &
    P1=$!
    
    sleep 3s
    should_trace=true
    while ! grep -q "Listening for transport dt_socket at address: $port" $exe_log
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
        bash tracing_2_tracer.sh $PROJECT_NAME $FUZZER $log_dir $port &> $tracer_log &
        P2=$!
        wait $P1 $P2
    fi
    echo Traced $p $f
    if [ $quit_after_one = true ]
    then
        break
    fi
done < $data_file | tqdm --total $(cat $data_file | wc -l) >> /dev/null

echo "Worker $worker_id/$num_workers (port $port) done. Logged to $log_dir."
