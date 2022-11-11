#!/bin/bash

# Before running:
# python3 infra/helper.py pull_images
# yes | python3 infra/helper.py build_image $PROJECT_NAME
# python3 infra/helper.py build_fuzzers --sanitizer $SAN --architecture $ARCH $PROJECT_NAME

# tomcat ELEvaluationFuzzer
CORPUS_ROOT="$1"
FUZZER_LOGS_ROOT="$2"
TIMEOUT="$3"
PROJECT_NAME="$4"
FUZZER="$5"
SAN="address"
ARCH="x86_64"

corpus_dir="$CORPUS_ROOT/$PROJECT_NAME/$SAN-$ARCH-$FUZZER"
rm -rf $corpus_dir
mkdir -p $corpus_dir

logfile="$FUZZER_LOGS_ROOT/$PROJECT_NAME-$SAN-$ARCH-$FUZZER.log"
mkdir -p $logfile

echo "Arguments: Project=$PROJECT_NAME Sanitizer=$SAN Architecture=$ARCH FuzzTarget=$FUZZER CorpusDir=$corpus_dir"

python infra/helper.py run_fuzzer --corpus-dir $corpus_dir $PROJECT_NAME $FUZZER max_total_time=$TIMEOUT seed=123 fork=1 ignore_crashes=1 2>&1 | tee $logfile

echo Finished with $?
