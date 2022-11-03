#!/bin/bash
# bash tracing_2_tracer.sh tomcat ELEvaluationFuzzer traces-1m

PROJECT_NAME="$1"
FUZZER="$2"
log_dir="$3"
PORT="$4"
TIMEOUT="30m"

mkdir -p $log_dir

tracer_jar="/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar"
log_file="$log_dir/trace-$PROJECT_NAME-$FUZZER.xml"

java -jar $tracer_jar -l $log_file -t dt_socket -p $PORT -m fuzzerTestOneInput &
PMAIN=$!

# wait for main process, kill if timeout
{ sleep $TIMEOUT; echo "TIMEOUT; KILLING $PMAIN"; kill -9 $PMAIN; pkill -9 -P $PMAIN; echo "<timeout/>" >> $log_file } &
wait $PMAIN
echo PMAIN $PMAIN exited with $?
kill -9 %%
