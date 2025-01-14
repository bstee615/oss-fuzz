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
rm -f $logfile

echo "Arguments: Project=$PROJECT_NAME Sanitizer=$SAN Architecture=$ARCH FuzzTarget=$FUZZER CorpusDir=$corpus_dir"

TIMEOUT="$(( ${TIMEOUT} * 30 ))"
python infra/helper.py run_fuzzer --corpus-dir $corpus_dir $PROJECT_NAME $FUZZER max_total_time=$TIMEOUT seed=123 jobs=8 workers=8 ignore_crashes=1 &
PMAIN=$!

to_remove="$(docker ps -q --filter name=fuzzmeister)"
{ sleep $TIMEOUT; echo "TIMEOUT; KILLING fuzzmeister and $PMAIN"; if [ ! -z "$to_remove" ]; then docker rm -f $to_remove; echo Removing containers $to_remove; fi; kill -9 $PMAIN; } &
wait $PMAIN
echo PMAIN $PMAIN exited with $?

exitcode=${PIPESTATUS[0]}
echo Finished with $exitcode

