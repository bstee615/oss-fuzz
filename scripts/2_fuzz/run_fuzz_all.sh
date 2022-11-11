#!/bin/bash

MINUTES=30 # number of minutes before timeout
TIMEOUT=$(( 60 * $MINUTES )) # number of seconds before timeout
CORPUS_ROOT=corpora-${MINUTES}m
FUZZER_LOGS_ROOT=fuzzlogs-${MINUTES}m
LOG_FILE=fuzz-${MINUTES}m.log
DATA_FILE="data/1_preprocess/java-projects-fuzzers-from-csv-fixed.txt"
PARALLEL=6

rm -rf $LOG_FILE $CORPUS_ROOT $FUZZER_LOGS_ROOT

parallel --progress --group -N 2 -j6 bash $(dirname $0)/run_fuzz.sh $CORPUS_ROOT $FUZZER_LOGS_ROOT $TIMEOUT ::: $(cat $DATA_FILE) > $LOG_FILE
