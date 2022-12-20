#!/bin/bash

#OPTIONS
quit_after_one=false

log_dir="$1"
base_port="$2"
worker_id="$3"
port=$(( $base_port + $worker_id ))
corpus_root="$4"
PROJECT_NAME="$5"
FUZZER="$6"
echo RUNNING $log_dir $base_port $worker_id $port $corpus_root $PROJECT_NAME $FUZZER
echo RUNNING $log_dir $base_port $worker_id $port $corpus_root $PROJECT_NAME $FUZZER > "$log_dir/${port}.status"
#OPTIONS

SAN="address"
ARCH="x86_64"

corpus_dir="$corpus_root/$PROJECT_NAME/$SAN-$ARCH-$FUZZER"
id="$PROJECT_NAME-$FUZZER"
exe_log="$log_dir/logs-exe/$id.log"
tracer_log="$log_dir/logs-tracer/$id.log"
xml_log="$log_dir/logs-xmls/trace-$PROJECT_NAME-$FUZZER.xml"

bash $(dirname $0)/../2_exe.sh $PROJECT_NAME $FUZZER $corpus_dir $port &> $exe_log &
P1=$!

sleep 3s
should_trace=true
rm -f $tracer_log
while ! grep -q "Listening for transport dt_socket at address: $port" $exe_log
do
    sleep 1s
    if [ ! -e /proc/$P1 ]
    then
        echo Process $P1 for $PROJECT_NAME-$FUZZER quit. Skipping.
        should_trace=false
        break
    fi
    echo Waiting on $P1 $exe_log for listener...
done &>> $tracer_log
if [ "$should_trace" = true ]
then
    bash $(dirname $0)/../2_tracer.sh $PROJECT_NAME $FUZZER $xml_log $port &>> $tracer_log &
    P2=$!
    wait $P1 $P2
fi
echo "$0: Done with $PROJECT_NAME $FUZZER"

echo "Worker $worker_id (port $port) done. Logged to $log_dir."
