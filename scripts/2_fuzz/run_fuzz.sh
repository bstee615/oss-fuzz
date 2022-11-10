#!/bin/bash

# Before running:
# python3 infra/helper.py pull_images
# yes | python3 infra/helper.py build_image $PROJECT_NAME
# python3 infra/helper.py build_fuzzers --sanitizer $SAN --architecture $ARCH $PROJECT_NAME

# tomcat ELEvaluationFuzzer
PROJECT_NAME="$1"
SAN="address"
# SAN="$2"
ARCH="x86_64"
# ARCH="$3"
FUZZER="$2"
# FUZZER="$4"

corpus_dir="corpora/$PROJECT_NAME/$SAN-$ARCH-$FUZZER"
rm -rf $corpus_dir
mkdir -p $corpus_dir

logfile="logs_fuzzing/$PROJECT_NAME-$SAN-$ARCH-$FUZZER.log"
mkdir -p logs_fuzzing

echo "Arguments: Project=$PROJECT_NAME Sanitizer=$SAN Architecture=$ARCH FuzzTarget=$FUZZER CorpusDir=$corpus_dir"

python3 infra/helper.py run_fuzzer --corpus-dir $corpus_dir $PROJECT_NAME $FUZZER max_total_time=60 seed=123 2>&1 | tee $logfile
