#!/bin/bash

set -e

BUILD_OUT_DIR="build/out"
DST_DIR="jar_code"

rm -r $DST_DIR

function unzipJars() {
    buildDir="$BUILD_OUT_DIR/$1"
    dstDir="$DST_DIR/$1"
    rm -rf $dstDir
    if [ -d $buildDir ]
    then
        for jarFile in $(find $buildDir -name '*.jar')
        do
            if [ ! $(basename $jarFile) = "jazzer_agent_deploy.jar" ]
            then
                # relative_path="$(realpath --relative-to="$BUILD_OUT_DIR" "$jarFile")"
                # dstDir="$DST_DIR/${relative_path%.jar}"
                echo "Unpacking $jarFile to $dstDir"
                timeout 10m jd-cli --displayLineNumbers --skipResources --outputDir ${dstDir} $jarFile || echo "TIMED OUT: $1 $jarFile"
            fi
        done
    else
        echo "Missing build directory: $buildDir"
    fi
}

if [ ! -z "$1" ]
then
    unzipJars $1
else
    while read p
    do
        unzipJars $p
    done < data/1_preprocess/java-projects-from-csv.txt
fi
