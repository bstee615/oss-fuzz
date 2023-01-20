#!/bin/bash
function getData() {
    # cat data/1_preprocess/java-projects-from-csv.txt
    head -n1 data/1_preprocess/java-projects-from-csv.txt
}
while read p
do
    echo BUILDING PROJECT $p... | tee -a build_all_fuzzers.log
    git checkout projects/$p &>> build_all_fuzzers.log
    python scripts/7_dual_implementation_2/modify_build_scripts.py $p &>> build_all_fuzzers.log
    bash scripts/0_misc/build_project_fuzzer.sh $p --no_cache_build_image &>> build_all_fuzzers.log
done < <(getData) | tqdm --total $(getData | wc -l)
