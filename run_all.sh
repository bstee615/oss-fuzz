#!/bin/bash

LOG_DIR="do_one_test_logs"
mkdir -p $LOG_DIR

DATA_FILE="data/1_preprocess/java-projects-fuzzers-from-csv.txt"

while read p
do
    PROJECT=$(echo $p | cut -d " " -f 1)
    FUZZER=$(echo $p | cut -d " " -f 2)
    timeout 30m bash scripts/7_dual_implementation_2/do_one_project.sh $PROJECT $FUZZER &> $LOG_DIR/${PROJECT}_${FUZZER}.log
    echo $p
done < $DATA_FILE | tqdm --total $(cat $DATA_FILE | wc -l)
