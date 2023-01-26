#!/bin/bash

set -e
set -x

PROJECT="$1"
FUZZER="$2"
# PROJECT="angus-mail"
# FUZZER="ASCIIUtilityFuzzer"

CORPUS_ROOT="/run/media/benjis/BASILISK/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/fuzz_run_5_complete/corpora-10m"
# CORPUS_ROOT="corpora-10m"
CORPUS_DIR="$CORPUS_ROOT/$PROJECT/address-x86_64-$FUZZER"
CORPUS_INPUT="$(ls -d $CORPUS_ROOT/$PROJECT/address-x86_64-$FUZZER/* | head -n1)"

RECORDER_LOG_DIR="recorder_logs"
rm -rf $RECORDER_LOG_DIR/
mkdir -p $RECORDER_LOG_DIR/

SOURCE_LOG_DIR="source_logs/$PROJECT/$FUZZER"
mkdir -p $SOURCE_LOG_DIR
SOURCE_PATH=$(find projects/$PROJECT -name $FUZZER.java)

FAILURE_LOG_FILE="$SOURCE_LOG_DIR/failures.txt"

# BUILD_ARGS=""
BUILD_ARGS="--shortcut --no-clean"

# Instrument fuzzer
git checkout projects/$PROJECT
cp $SOURCE_PATH $SOURCE_LOG_DIR/${FUZZER}.java.01_original
echo "Instrumenting $PROJECT $FUZZER..."
python $(dirname $0)/modify_build_scripts.py $PROJECT || (echo "$PROJECT $FUZZER modify_build_scripts.py" >> $FAILURE_LOG_FILE && exit 1)
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
    --write \
    --mode INSTRUMENT --fuzzerName $FUZZER \
    --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs --baseLoggingDir /recorder \
     || (echo "$PROJECT $FUZZER transformer-INSTRUMENT" >> $FAILURE_LOG_FILE && exit 1)
cp $SOURCE_PATH $SOURCE_LOG_DIR/${FUZZER}.java.02_instrumented
bash $(dirname $(dirname $0))/0_misc/build_project_fuzzer.sh $PROJECT $BUILD_ARGS || (echo "$PROJECT $FUZZER build_fuzzer-INSTRUMENT" >> $FAILURE_LOG_FILE && exit 1)

# Run with tracer
echo "Running $PROJECT $FUZZER with input $CORPUS_DIR..."
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $CORPUS_DIR timeout=300 instrumentation_excludes="**" || (echo "$PROJECT $FUZZER reproduce-INSTRUMENT" >> $FAILURE_LOG_FILE && exit 1)
for f in $RECORDER_LOG_DIR/*.jsonl
do
    jq --slurp < $f > ${f%.jsonl}.json
done
cp -r $RECORDER_LOG_DIR $SOURCE_LOG_DIR

# # Reset, then hardcode fuzzer
# echo "Hardcoding $PROJECT $FUZZER with input from $RECORDER_LOG_DIR and running with input $CORPUS_DIR..."
# git checkout projects/$PROJECT
# java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
#     --write \
#     --mode HARDCODE --fuzzerName $FUZZER \
#     --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs \
#     --inputFile $RECORDER_LOG_DIR/fuzzerOutput_$FUZZER.json --resultFile $RECORDER_LOG_DIR/fuzzerResult_$FUZZER.json || (echo "$PROJECT $FUZZER transformer-HARDCODE" >> $FAILURE_LOG_FILE && exit 1)
# cp $SOURCE_PATH $SOURCE_LOG_DIR/${FUZZER}.java.03_hardcoded
# bash $(dirname $(dirname $0))/0_misc/build_project_fuzzer.sh $PROJECT $BUILD_ARGS || (echo "$PROJECT $FUZZER build_fuzzer-HARDCODE" >> $FAILURE_LOG_FILE && exit 1)
# python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $CORPUS_INPUT timeout=300 instrumentation_excludes="**" || (echo "$PROJECT $FUZZER reproduce-HARDCODE" >> $FAILURE_LOG_FILE && exit 1)
