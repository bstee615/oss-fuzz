#!/bin/bash

PROJECT="$1"
FUZZER="$2"

set -e

# python modify_build_scripts.py $PROJECT
# java -jar transformer/build/libs/transformer-1.0-SNAPSHOT.jar projects/$PROJECT/

echo N | python3 infra/helper.py build_image $PROJECT
python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $PROJECT

python3 infra/helper.py reproduce --num_runs 1 --container_name foo $PROJECT $FUZZER \
    corpus-test/$PROJECT/1b02207ba9e9671cce31ec2e155dbed229efb79a instrumentation_excludes="**" 2>&1 \
    | tee do_one_project_output.txt \
    | bash print_fuzzeroutput.sh | jq --slurp > do_one_project_output.json
