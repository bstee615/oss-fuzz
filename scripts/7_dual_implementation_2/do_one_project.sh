#!/bin/bash

# PROJECT="$1"
# FUZZER="$2"
# LOG_NAME="$3"
PROJECT="angus-mail"
FUZZER="ASCIIUtilityFuzzer"
LOG_NAME="do_one_test/log"

TXT_FILE="$LOG_NAME.txt"
JSON_FILE="$LOG_NAME.json"
TRACER_LOG_FILE="${LOG_NAME}_tracer.txt"
XML_FILE="$LOG_NAME.xml"
RESULTS_JSON_FILE="${LOG_NAME}_results.json"
HARDCODED_TXT_FILE="${LOG_NAME}_hardcoded.txt"
HARDCODED_JSON_FILE="${LOG_NAME}_hardcoded.json"

XML_FILE_2="${LOG_NAME}_2.xml"
TRACER_LOG_FILE_2="${LOG_NAME}_tracer2.txt"

CORPUS_ROOT="/run/media/benjis/BASILISK/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/fuzz_run_5_complete/corpora-10m"

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
echo "Running $PROJECT $FUZZER -> $JSON_FILE"
FIRST_CORPUS_INPUT="$(ls -d $CORPUS_ROOT/$PROJECT/address-x86_64-$FUZZER/* | head -n1)"
rm recorder_logs/*.{jsonl,json}
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $FIRST_CORPUS_INPUT timeout=300 instrumentation_excludes="**"
for f in recorder_logs/*.jsonl
do
    jq --slurp < $f > ${f%.jsonl}.json
done

# Reset, then hardcode fuzzer
git checkout projects/$PROJECT
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
    --write \
    --mode HARDCODE --fuzzerName $FUZZER \
    --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs \
    --inputFile recorder_logs/fuzzerOutput_ASCIIUtilityFuzzer.json --resultFile recorder_logs/fuzzerResult_ASCIIUtilityFuzzer.json
build_fuzzer $PROJECT
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $FIRST_CORPUS_INPUT timeout=300 instrumentation_excludes="**"
