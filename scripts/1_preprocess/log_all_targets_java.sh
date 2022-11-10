#!/bin/bash

# head -n 1 java-projects-from-csv.txt | \
cat java-projects-from-csv.txt | \
    while read p
do
    echo $p
    find projects/$p -name '*.java' | xargs basename -s .java > projects/$p/fuzzers.txt
done
