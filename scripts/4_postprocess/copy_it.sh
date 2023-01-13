#!/bin/bash
# Copy source code from docker images

function copyIt() {
    project=$1
    echo "Copying files for $project..."
    id=$(docker create gcr.io/oss-fuzz/$project)
    docker cp $id:$(docker inspect --format='{{.Config.WorkingDir}}' $id) repos_build/$project
    docker rm -v $id >> /dev/null
}

if [ ! -z "$1" ]
then
    copyIt $1
else
    while read p
    do
        copyIt $p
    done < data/1_preprocess/java-projects-from-csv.txt
fi
