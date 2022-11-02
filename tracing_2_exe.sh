#!/bin/bash
# bash tracing_2_exe.sh tomcat ELEvaluationFuzzer corpus/tomcat-ELEvaluationFuzzer

PROJECT_NAME="$1"
FUZZER="$2"
CORPUS_DIR="$3"

if [ ! -d $CORPUS_DIR ]
then
    exec ls $CORPUS_DIR
fi

python3 infra/helper.py reproduce --tracer --num_runs 1 $PROJECT_NAME $FUZZER $CORPUS_DIR timeout=300
