#!/bin/bash
# bash tracing_2_exe.sh tomcat ELEvaluationFuzzer corpus/tomcat-ELEvaluationFuzzer

PROJECT_NAME="$1"
FUZZER="$2"
CORPUS_DIR="$3"
PORT="$4"
TIMEOUT="30m"

if [ ! -d $CORPUS_DIR ]
then
    exec ls $CORPUS_DIR
fi

olddockers=$(docker ps -q)

python3 infra/helper.py reproduce --tracer --num_runs 1 --tracer_port $PORT $PROJECT_NAME $FUZZER $CORPUS_DIR timeout=1800 instrumentation_excludes="**" &
PMAIN=$!

# wait for docker container to start up, log ID
sleep 10s
newdockers=$(docker ps -q)
diffdockers=$(python3 diffroomba.py OLD $olddockers NEW $newdockers)
echo Launched docker containers: $diffdockers

# wait for main process, kill if timeout
{ sleep $TIMEOUT; echo "TIMEOUT; KILLING $diffdockers and $PMAIN"; docker rm -f $diffdockers; kill -9 $PMAIN; pkill -9 -P $PMAIN; } &
wait $PMAIN
echo PMAIN $PMAIN exited with $?
kill -9 %%
