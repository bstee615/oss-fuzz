#!/bin/bash

PROJECT_NAME="$1"
FUZZER="$2"
CORPUS_DIR="$3"

rm -rf $CORPUS_DIR
mkdir -p $CORPUS_DIR

timeout 5m python3 infra/helper.py run_fuzzer $PROJECT_NAME $FUZZER --corpus-dir $CORPUS_DIR
