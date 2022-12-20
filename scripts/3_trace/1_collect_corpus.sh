#!/bin/bash

PROJECT_NAME="$1"
FUZZER="$2"
WORKER_ID="$3"
CORPUS_DIR="$4"

LOG_FILE="$CORPUS_DIR/logs/run_fuzzer-$PROJECT_NAME-$FUZZER.log"
CORPUS_DIR="$CORPUS_DIR/$PROJECT_NAME/$FUZZER"

# rm -rf $CORPUS_DIR
mkdir -p $CORPUS_DIR
if [ $(ls $CORPUS_DIR | wc -l) -gt 100 ]
then
    echo "HIT ENOUGH FILES IN CORPUS FOR $PROJECT_NAME $FUZZER ... SKIPPING"
    exit 123
fi

timeout 10m python3 infra/helper.py run_fuzzer $PROJECT_NAME $FUZZER --corpus-dir $CORPUS_DIR --worker-id $WORKER_ID 2>&1 | tee "$LOG_FILE"
