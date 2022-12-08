#!/bin/bash
# bash tracing_2_tracer.sh tomcat ELEvaluationFuzzer traces-1m

PROJECT_NAME="$1"
FUZZER="$2"
log_file="$3"
PORT="$4"
TIMEOUT="180m"

tracer_jar="/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar"

java -jar $tracer_jar -l $log_file -t dt_socket -p $PORT -m fuzzerTestOneInput -v DEBUG &
PMAIN=$!

# wait for main process, kill if timeout
{ sleep $TIMEOUT; echo "$0: TIMEOUT; KILLING $PMAIN"; kill -9 $PMAIN; pkill -9 -P $PMAIN; sleep 10s; echo "<timeout/>" >> $log_file; } &
wait $PMAIN
echo "$0: PMAIN $PMAIN exited with $?"
kill -9 %%
