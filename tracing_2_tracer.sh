#!/bin/bash
# bash tracing_2_tracer.sh tomcat ELEvaluationFuzzer corpus/tomcat-ELEvaluationFuzzer

PROJECT_NAME="$1"
FUZZER="$2"
CORPUS_DIR="$3"

python3 infra/helper.py reproduce --tracer --num_runs 1 $PROJECT_NAME $FUZZER $CORPUS_DIR timeout=300
