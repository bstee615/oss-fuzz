#!/bin/bash -eux

KILLED="$(cat killed_overtime.txt)"

while true
do 
    clear
    
    yesterday=$(date "+%s" -d "630 sec ago")
    echo Pruning containers older than $(date -d "@$yesterday")...

    # dnsdock should not be stopped : we limit to the containers created after it
    docker ps --filter name=fuzzmeister --no-trunc --format 'table {{.ID}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Ports}}'
    echo ALREADY KILLED $(( $(echo $KILLED | wc -l) - 1 ))
    echo $KILLED
    docker ps --filter name=fuzzmeister -q --format "{{.ID}} {{.CreatedAt}}" | while read line
    do
        # line looks like:
        # 123456789abcdef 2017-01-01 00:00:00 +02:00 CEST
        set $line
        id=$1
        # date doesn't like the CEST part so we skip it
        date=$(date -d "$(echo ${@:2:3})" +%s)
        if [ "$date" -le "$yesterday" ]; then
            this_killed="$id:$(docker inspect $id -f '{{.Config.Cmd}}')"
            echo $this_killed
            echo $this_killed >> killed_overtime.txt
            KILLED="$KILLED\n$this_killed"
            docker rm -f $id
        fi
    done

    sleep 5
done

# https://docs.docker.com/engine/reference/commandline/system_prune/
# This prunes images! do not use
# docker image prune --filter "until=10m"
