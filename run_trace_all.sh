#!/bin/bash

rm -f trace_all_*.log

while read p
do
    while read f
    do
        echo running $p $f... >> trace_all_exe.log
        PROJECT_NAME="$p"
        FUZZER="$f"
        SAN="address"
        SAN="x86_64"
        corpus_dir="corpora/$PROJECT_NAME/$SAN-$ARCH-$FUZZER"

        tracer_jar="/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar"

        CLASS_PATTERN="com.sun.mail.*"  # TODO: figure out class to trace!

        bash tracing_2_tracer.sh $PROJECT_NAME $FUZZER corpora/$PROJECT_NAME/$SAN-$ARCH-$FUZZER &>> trace_all_exe.log &
        P1=$!
        sleep 5s
        java -jar $tracer_jar -l traces/trace-$PROJECT_NAME-$FUZZER.xml -t dt_socket -p 8787 -v -c "$CLASS_PATTERN" &>> trace_all_tracer.log &
        P2=$!
        wait $P1 $P2

        break
    done < projects/$p/fuzzers.txt
    break
done < java-projects-from-csv.txt | tqdm --total $(cat projects/*/fuzzers.txt | wc -l) >> /dev/null
