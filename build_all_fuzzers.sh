#!/bin/bash
function getData() {
    cat data/1_preprocess/java-projects-from-csv.txt
    # head -n1 data/1_preprocess/java-projects-from-csv.txt
}
if [ ! -z "$1" ]
then
    LOG_FILE="build_all_fuzzers_${1}.log"
else
    LOG_FILE="build_all_fuzzers.log"
fi
while read p
do
    if [ ! -z "$1" ] && [ $p != "$1" ]
    then
        continue
    fi
    set -x
    bash scripts/0_misc/build_project_fuzzer.sh $p --no_cache_build_image --clean
    set +x
done < <(getData) 2>&1 | tee $LOG_FILE #| grep "DONE BUILDING PROJECT" | tqdm --total $(getData | wc -l)
