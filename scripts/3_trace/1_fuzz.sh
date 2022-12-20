#!/bin/bash

IN_FILE="01_build_errors_clean.txt"
OUT_DIR="corpora-10m-missing"

docker ps --filter name="fuzzmeister.*" -q | xargs docker rm -f
rm -rf $OUT_DIR
mkdir -p $OUT_DIR/logs

parallel --progress --group -N 2 -j4 \
    bash scripts/2_fuzz/run_fuzz.sh corpora-10m-missing corpora-10m-missing/logs 600 "{}" "{%}" \
    ::: $(cat $IN_FILE) \
    2>&1 | tee fuzz_missing.log
