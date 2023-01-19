while read p
do
    PROJECT=$(echo $p | cut -d " " -f 1)
    FUZZER=$(echo $p | cut -d " " -f 2)
    timeout 30m bash scripts/7_dual_implementation_2/do_one_project.sh $PROJECT $FUZZER &> do_one_test_${PROJECT}_${FUZZER}.log
    echo $p
# done < <(head -n 10 data/1_preprocess/java-projects-fuzzers-from-csv.txt) | tqdm --total 10 --desc running...
done < data/1_preprocess/java-projects-fuzzers-from-csv.txt | tqdm --total $(cat data/1_preprocess/java-projects-fuzzers-from-csv.txt | wc -l) --desc running...
