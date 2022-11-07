logs_dir="$1"
grep -h -E "<call.*" $logs_dir/*.xml | grep -vi Fuzzer | wc -l
