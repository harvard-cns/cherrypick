#!/bin/bash

IFS=$'\n' GLOBIGNORE='*' vmn=($(cat mapping | awk '{print $2}'))
IFS=$'\n' GLOBIGNORE='*' vms=($(cat mapping | awk '{print $1}'))

LEN=$((${#vms[@]}-1))

for i in `seq 0 $LEN`; do
    for j in `seq 0 $LEN`; do
        [[ $i == $j ]] && continue

        srcip=${vms[$i]}
        dstip=${vms[$j]}

        basedir=${vmn[$i]}-proc/proc/net
        basedirj=${vmn[$j]}-proc/proc/net

        echo $basedir/$srcip/$dstip/sbytes

        cat $basedir/$srcip/$dstip/sbytes  | awk -F',' '{sum += $2} END {print sum}'
        cp $basedir/$dstip/$srcip/sbytes  $basedir/$srcip/$dstip/rbytes
        #cat $basedirj/$srcip/$dstip/sbytes | awk -F',' '{sum += $2} END {print sum}'
    done
done
