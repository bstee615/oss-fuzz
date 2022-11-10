#!/bin/bash
for s in $(grep -R "instrumentation_includes=" projects)
do
    if echo $s | grep -q :
    then
        # echo $s

        # from projects
        projectname=$(echo $s | cut -d':' -f1 | xargs dirname)
        package=$(echo $s | cut -d':' -f2 | grep -Eo '=.*\.\*' | head -c-3 | rev | head -c-1 | rev)
        echo -n $package > $projectname/package_name.txt
    fi
done
