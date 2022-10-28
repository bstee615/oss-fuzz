#!/bin/bash

rm -f fuzz_all.log

while read p
do
    while read f
    do
        echo running $p $f...
        timeout -s SIGINT 70 bash run_fuzz.sh $p $f &>> fuzz_all.log
    done < projects/$p/fuzzers.txt
done < java-projects-from-csv.txt | tqdm --total $(cat projects/*/fuzzers.txt | wc -l) >> /dev/null
