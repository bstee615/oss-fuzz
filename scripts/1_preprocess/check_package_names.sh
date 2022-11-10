#!/bin/bash

while read p
do
    touch "projects/$p/package_name.txt"
    if [ -s "projects/$p/package_name.txt" ]
    then
        # echo "*** projects/$p/package_name.txt" $files
        # cat projects/$p/package_name.txt
        echo -n ""
    else
        files=$(find projects/$p -name '*.java')
        echo "*** projects/$p/package_name.txt" $files
        if [ ! -z "$files" ]
        then
            cat $files | grep import | grep $p 
        fi
    fi
done < java-projects-from-csv.txt
