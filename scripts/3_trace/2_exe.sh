#!/bin/bash
# bash tracing_2_exe.sh tomcat ELEvaluationFuzzer corpus/tomcat-ELEvaluationFuzzer

PROJECT_NAME="$1"
FUZZER="$2"
CORPUS_DIR="$3"
PORT="$4"
TIMEOUT="180m"

if [ ! -d $CORPUS_DIR ]
then
    exec ls $CORPUS_DIR
fi

docker_name="reproduce_${PORT}"
docker rm -f "reproduce_${PORT}"

python3 infra/helper.py reproduce --tracer --num_runs 1 --tracer_port $PORT --container_name $docker_name $PROJECT_NAME $FUZZER $CORPUS_DIR timeout=3600 instrumentation_excludes="**" &
PMAIN=$!

# wait for main process, kill if timeout
{ sleep $TIMEOUT; dockers=$(docker ps -q --filter name=$docker_name); echo Launched docker containers: $dockers; echo "$0: TIMEOUT; KILLING $dockers and $PMAIN"; docker rm -f $dockers; kill -9 $PMAIN; pkill -9 -P $PMAIN; } &
wait $PMAIN
echo "$0: PMAIN $PMAIN exited with $?"
kill -9 %%
