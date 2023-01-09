#!/bin/bash

PROJECT="$1"
FUZZER="$2"
LOG_NAME="$3"
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
python modify_build_scripts.py $PROJECT
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar --mode INSTRUMENT --fuzzerDir projects/$PROJECT/ --fuzzerName $FUZZER
build_fuzzer $PROJECT

# Run with tracer
echo "Tracing $PROJECT $FUZZER -> $JSON_FILE"
(python3 infra/helper.py reproduce --tracer --tracer_port 8000 --num_runs 1 --container_name foo $PROJECT $FUZZER \
    $CORPUS_ROOT/$PROJECT/address-x86_64-$FUZZER timeout=300 instrumentation_excludes="**" 2>&1 \
    | tee $TXT_FILE \
    | bash print_fuzzeroutput.sh | jq --slurp) > $JSON_FILE &
sleep 10s
(java -jar ../trace-modeling/trace_collection_java/app/build/libs/tracer.jar \
    -t dt_socket -p 8000 -m fuzzerTestOneInput -v DEBUG \
    -l $XML_FILE 2>&1 | tee $TRACER_LOG_FILE) &
wait

# Postprocess results
python transform_xml_to_callresults.py $XML_FILE $RESULTS_JSON_FILE
read -p "MODIFY HARNESS using $RESULTS_JSON_FILE, then Press enter to continue"

# Reset, then hardcode fuzzer
git checkout projects/$PROJECT
echo "Hardcoding inputs $PROJECT $FUZZER..."
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar --mode HARDCODE --fuzzerDir projects/$PROJECT/ --fuzzerName $FUZZER --jsonFile $JSON_FILE --resultFile $RESULTS_JSON_FILE
build_fuzzer $PROJECT
