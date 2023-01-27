#!/bin/bash

# build_dir="build"
build_dir="build_test"

# corpus_dir="autofuzz"
corpus_dir="autofuzz_test"

timeout="600"

set -e

IFS=$'\n'
for pf in $(cat data/1_preprocess/java-projects-fuzzers-from-csv.txt)
do
project="$(echo $pf | cut -d' ' -f1)"
fuzzer="$(echo $pf | cut -d' ' -f2)"
# for line in $(jq -r '.[][].method' $build_dir/out/$project/*.jar.class_manifest.json)  # select all methods
for line in $(jq -r '.[][] | select(.all_primitive==true) | .method' $build_dir/out/$project/*.jar.class_manifest.json)  # select only methods where all_primitive == true
do
bash $(dirname $0)/run_autofuzz_one.sh "$project" "$fuzzer" "$line" "$timeout" "$build_dir" "$corpus_dir"
done
done
