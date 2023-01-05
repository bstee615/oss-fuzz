#!/bin/bash
# bash tracing_2_tracer.sh tomcat ELEvaluationFuzzer traces-1m

PROJECT_NAME="$1"
FUZZER="$2"
log_file="$3"
PORT="$4"
TIMEOUT="180m"

tracer_jar="/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/app/build/libs/tracer.jar"

java -jar $tracer_jar -l $log_file -t dt_socket -p $PORT -m fuzzerTestOneInput -v DEBUG &
PMAIN=$!

docker_name="reproduce_${PORT}_${PROJECT_NAME}_${FUZZER}"
# wait for main process, kill if timeout
kill_if_exe_done(){
  sleep 10s
  while true
  do
    [ `pgrep $PMAIN` ] || return
    if [ -z "$(docker ps -q --filter name=$docker_name)" ]
    then
        echo "$0: EXE DONE; KILLING $PMAIN"
        kill -9 $PMAIN
        break
    fi
    sleep 10s
  done
}
kill_if_exe_done &
{ sleep $TIMEOUT; echo "$0: TIMEOUT; KILLING $PMAIN"; kill -9 $PMAIN; pkill -9 -P $PMAIN; sleep 10s; } &
wait $PMAIN
echo "$0: PMAIN $PMAIN exited with $?"
kill -9 %%
