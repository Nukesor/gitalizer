#!/usr/bin/bash

cwd=$(pwd)

cd /tmp/gitalizer

for file in *; do
    cd $file
    count=$(ls -l | wc -l)
    if [ $count -eq '1' ] ; then
        lol=$count
        cd ..
        rm -r $file
    else
        echo $file
        cd ..
    fi
done
