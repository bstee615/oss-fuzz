#!/bin/bash

project="angus-mail"
fuzzer="ASCIIUtilityFuzzer"
while read line
do
    line="$(echo $line | sed -E 's/\s+//g')"
    # line="$(echo $line | sed 's/^.\(.*\).$/\1/')"
    corpus_dir="corpus_test_autofuzz/$project/$fuzzer/$(echo $line | sed 's/::/__/g')"
    echo "AUTOFUZZING $line into $corpus_dir..."
    docker run --rm --privileged --shm-size=2g --platform linux/amd64 \
        -e FUZZING_ENGINE=libfuzzer -e SANITIZER=address -e RUN_FUZZER_MODE=interactive -e HELPER=True \
        -v "/home/benjis/code/bug-benchmarks/oss-fuzz/$corpus_dir:/tmp/ASCIIUtilityFuzzer_corpus" \
        -v "/home/benjis/code/bug-benchmarks/oss-fuzz/build/out/$project:/out" \
        -t gcr.io/oss-fuzz-base/base-runner \
        run_fuzzer ASCIIUtilityFuzzer -max_total_time=30 -seed=123 -ignore_crashes=1 \
        "--autofuzz='$line'" \
        "--autofuzz_ignore='java.lang.*,com.code_intelligence.*,java.net.*'"
done < <(jq -r '.[][].method' build/out/$project/*.jar.class_manifest.json | head -n5)