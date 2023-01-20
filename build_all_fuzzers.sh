while read p
do
    echo BUILDING PROJECT $p...
    bash scripts/0_misc/build_project_fuzzer.sh $p --no_cache_build_image &>> build_all_fuzzers.log
done < data/1_preprocess/java-projects-from-csv.txt
