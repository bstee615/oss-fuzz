#!/bin/bash

PROJECT="$1"
FUZZER="$2"
# PROJECT="angus-mail"
# FUZZER="ASCIIUtilityFuzzer"

CORPUS_ROOT="/run/media/benjis/BASILISK/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/fuzz_run_5_complete/corpora-10m"
CORPUS_INPUT="$(ls -d $CORPUS_ROOT/$PROJECT/address-x86_64-$FUZZER/* | head -n1)"

RECORDER_LOG_DIR="recorder_logs"
mkdir -p $RECORDER_LOG_DIR/

set -e
set -x

function build_fuzzer() {
    echo N | python3 infra/helper.py build_image $1
    python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $1
}

# Instrument fuzzer
git checkout projects/$PROJECT
echo "Instrumenting $PROJECT $FUZZER..."
python $(dirname $0)/modify_build_scripts.py $PROJECT
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
    --write \
    --mode INSTRUMENT --fuzzerName $FUZZER \
    --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs --baseLoggingDir /recorder
build_fuzzer $PROJECT

# Run with tracer
echo "Running $PROJECT $FUZZER with input $CORPUS_INPUT..."
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $CORPUS_INPUT timeout=300 instrumentation_excludes="**"
for f in $RECORDER_LOG_DIR/*.jsonl
do
    jq --slurp < $f > ${f%.jsonl}.json
done

# Reset, then hardcode fuzzer
echo "Hardcoding $PROJECT $FUZZER with input from $RECORDER_LOG_DIR and running with input $CORPUS_INPUT..."
git checkout projects/$PROJECT
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
    --write \
    --mode HARDCODE --fuzzerName $FUZZER \
    --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs \
    --inputFile $RECORDER_LOG_DIR/fuzzerOutput_ASCIIUtilityFuzzer.json --resultFile $RECORDER_LOG_DIR/fuzzerResult_ASCIIUtilityFuzzer.json
build_fuzzer $PROJECT
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $CORPUS_INPUT timeout=300 instrumentation_excludes="**"
