logs_dir="$1"
echo EXECUTABLE
grep -e PMAIN $logs_dir/logs-exe/*.log | rev | cut -d' ' -f1 | rev | sort | uniq -c
echo failed port $(grep "driver failed programming external connectivity" $logs_dir/logs-exe/*.log | wc -l)
echo TRACER
grep -e PMAIN $logs_dir/logs-tracer/*.log | rev | cut -d' ' -f1 | rev | sort | uniq -c
