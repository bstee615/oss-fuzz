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
    set -x
    if [ ! -z "$1" ] && [p != "$1" ]
    then
        echo "SKIPPING PROJECT $p (ONLY BUILDING $1)..."
        continue
    fi
    echo BEGIN BUILDING PROJECT $p...
    git checkout projects/$p
    python scripts/7_dual_implementation_2/modify_build_scripts.py $p
    (bash scripts/0_misc/build_project_fuzzer.sh $p --no_cache_build_image --clean || echo $p >> build_failed.log)
    python scripts/7_dual_implementation_2/modify_generated_build_scripts.py $p
    git checkout projects/$p
    echo DONE BUILDING PROJECT $p...
done < <(getData) 2>&1 | tee $LOG_FILE #| grep "DONE BUILDING PROJECT" | tqdm --total $(getData | wc -l)
