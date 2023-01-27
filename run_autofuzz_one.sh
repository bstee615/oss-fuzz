#!/bin/bash

project="$1"
fuzzer="$2"
line="$3"
max_total_time="$4"
build_dir="$5"
corpus_dir="$6"
line="$(echo $line | sed -E 's/\s+//g')"
corpus_dir="$corpus_dir/$project/$fuzzer/$(echo $line | sed 's/::/__/g')"
echo "AUTOFUZZING $line into $corpus_dir..."
docker run --rm --privileged --shm-size=2g --platform linux/amd64 -i \
    -e FUZZING_ENGINE=libfuzzer -e SANITIZER=address -e RUN_FUZZER_MODE=interactive -e HELPER=True \
    -v "/home/benjis/code/bug-benchmarks/oss-fuzz/$corpus_dir:/tmp/ASCIIUtilityFuzzer_corpus" \
    -v "/home/benjis/code/bug-benchmarks/oss-fuzz/$build_dir/out/$project:/out" \
    -t gcr.io/oss-fuzz-base/base-runner \
    run_fuzzer ASCIIUtilityFuzzer -max_total_time="$max_total_time" -seed=123 -jobs=20 -workers=10 -ignore_crashes=1 \
    "--autofuzz='$line'" \
    "--autofuzz_ignore='java.lang.*,com.code_intelligence.*,java.net.*,java.io.*,java.text.*'"
