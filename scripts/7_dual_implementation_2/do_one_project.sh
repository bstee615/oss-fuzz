#!/bin/bash

PROJECT="$1"
FUZZER="$2"
# PROJECT="angus-mail"
# FUZZER="ASCIIUtilityFuzzer"

CORPUS_ROOT="/run/media/benjis/BASILISK/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/fuzz_run_5_complete/corpora-10m"
CORPUS_INPUT="$(ls -d $CORPUS_ROOT/$PROJECT/address-x86_64-$FUZZER/* | head -n1)"

RECORDER_LOG_DIR="recorder_logs"
rm -rf $RECORDER_LOG_DIR/
mkdir -p $RECORDER_LOG_DIR/

SOURCE_LOG_DIR="source_logs/$PROJECT/$FUZZER/$(basename $CORPUS_INPUT)"
mkdir -p $SOURCE_LOG_DIR
SOURCE_PATH=$(find projects/$PROJECT -name $FUZZER.java)

set -x

function build_fuzzer() {
    echo N | python3 infra/helper.py build_image $1 || return 1
    python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $1 || return 1
}

# Instrument fuzzer
git checkout projects/$PROJECT
cp $SOURCE_PATH $SOURCE_LOG_DIR/${FUZZER}.java.01_original
echo "Instrumenting $PROJECT $FUZZER..."
python $(dirname $0)/modify_build_scripts.py $PROJECT || (echo "$PROJECT $FUZZER modify_build_scripts.py" >> $SOURCE_LOG_DIR/failures.txt && exit 1)
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
    --write \
    --mode INSTRUMENT --fuzzerName $FUZZER \
    --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs --baseLoggingDir /recorder \
     || (echo "$PROJECT $FUZZER transformer-INSTRUMENT" >> $SOURCE_LOG_DIR/failures.txt && exit 1)
cp $SOURCE_PATH $SOURCE_LOG_DIR/${FUZZER}.java.02_instrumented
build_fuzzer $PROJECT || (echo "$PROJECT $FUZZER build_fuzzer-INSTRUMENT" >> $SOURCE_LOG_DIR/failures.txt && exit 1)

# Run with tracer
echo "Running $PROJECT $FUZZER with input $CORPUS_INPUT..."
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $CORPUS_INPUT timeout=300 instrumentation_excludes="**" || (echo "$PROJECT $FUZZER reproduce-INSTRUMENT" >> $SOURCE_LOG_DIR/failures.txt && exit 1)
for f in $RECORDER_LOG_DIR/*.jsonl
do
    jq --slurp < $f > ${f%.jsonl}.json
done
cp -r $RECORDER_LOG_DIR $SOURCE_LOG_DIR

# Reset, then hardcode fuzzer
echo "Hardcoding $PROJECT $FUZZER with input from $RECORDER_LOG_DIR and running with input $CORPUS_INPUT..."
git checkout projects/$PROJECT
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar \
    --write \
    --mode HARDCODE --fuzzerName $FUZZER \
    --fuzzerDir projects/$PROJECT/ --jarDir build/out/$PROJECT/ --jarDir recorder/lib/build/libs \
    --inputFile $RECORDER_LOG_DIR/fuzzerOutput_$FUZZER.json --resultFile $RECORDER_LOG_DIR/fuzzerResult_$FUZZER.json || (echo "$PROJECT $FUZZER transformer-HARDCODE" >> $SOURCE_LOG_DIR/failures.txt && exit 1)
cp $SOURCE_PATH $SOURCE_LOG_DIR/${FUZZER}.java.03_hardcoded
build_fuzzer $PROJECT || (echo "$PROJECT $FUZZER build_fuzzer-HARDCODE" >> $SOURCE_LOG_DIR/failures.txt && exit 1)
python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER $CORPUS_INPUT timeout=300 instrumentation_excludes="**" || (echo "$PROJECT $FUZZER reproduce-HARDCODE" >> $SOURCE_LOG_DIR/failures.txt && exit 1)
