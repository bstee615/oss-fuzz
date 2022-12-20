#!/bin/bash

# head -n 1 java-projects-from-csv.txt | \
cat 05_to_build.txt | \
    while read p
do
    echo N | python3 infra/helper.py build_image $p
    echo $p $? >> build/build_image.txt
    python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $p
    echo $p $? >> build/build_fuzzers.txt
done
