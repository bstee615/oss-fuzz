#!/bin/bash

while read p
do
    while read f
    do
        echo $p $f
    done < projects/$p/fuzzers.txt
done < java-projects-from-csv.txt
