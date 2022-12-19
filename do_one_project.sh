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

set -e
set -x

git checkout projects/$PROJECT

echo "Instrumenting $PROJECT $FUZZER..."
python modify_build_scripts.py $PROJECT
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar --mode INSTRUMENT --fuzzerDir projects/$PROJECT/ --fuzzerName $FUZZER

echo N | python3 infra/helper.py build_image $PROJECT
python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $PROJECT

(python3 infra/helper.py reproduce --tracer --tracer_port 8000 --num_runs 1 --container_name foo $PROJECT $FUZZER \
    corpus-test/$PROJECT/1b02207ba9e9671cce31ec2e155dbed229efb79a timeout=300 instrumentation_excludes="**" 2>&1 \
    | tee $TXT_FILE \
    | bash print_fuzzeroutput.sh | jq --slurp) > $JSON_FILE &

echo "WAITING FOR CONTAINER TO START" && sleep 10s

(java -jar /run/media/benjis/FSCOPY/17537297-282f-49b5-b466-0f3332b732f8/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar \
    -t dt_socket -p 8000 -m fuzzerTestOneInput -v DEBUG \
    -l $XML_FILE 2>&1 | tee $TRACER_LOG_FILE) &

wait

python transform_xml_to_callresults.py $XML_FILE $RESULTS_JSON_FILE
read -p "MODIFY HARNESS using $RESULTS_JSON_FILE, then Press enter to continue"

echo "Hardcoding inputs $PROJECT $FUZZER..."
java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar --mode HARDCODE --fuzzerDir projects/$PROJECT/ --fuzzerName $FUZZER --jsonFile $JSON_FILE

echo N | python3 infra/helper.py build_image $PROJECT
python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $PROJECT

(python3 infra/helper.py reproduce --tracer --tracer_port 8000 --num_runs 1 --container_name foo $PROJECT $FUZZER \
    corpus-test/$PROJECT/1b02207ba9e9671cce31ec2e155dbed229efb79a instrumentation_excludes="**" 2>&1 \
    | tee $HARDCODED_TXT_FILE) &

echo "WAITING FOR CONTAINER TO START" && sleep 10s

(java -jar /run/media/benjis/FSCOPY/17537297-282f-49b5-b466-0f3332b732f8/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar \
    -t dt_socket -p 8000 -m fuzzerTestOneInput -v DEBUG \
    -l $XML_FILE_2 2>&1 | tee $TRACER_LOG_FILE_2) &

wait
