#!/bin/bash
# bash tracing_2_tracer.sh tomcat ELEvaluationFuzzer traces-1m

PROJECT_NAME="$1"
FUZZER="$2"
log_dir="$3"
PORT="$4"

mkdir -p $log_dir

tracer_jar="/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar"

exec timeout 1h java -jar $tracer_jar -l $log_dir/trace-$PROJECT_NAME-$FUZZER.xml -t dt_socket -p $PORT
