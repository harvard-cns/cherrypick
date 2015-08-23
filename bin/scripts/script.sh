#!/bin/bash

base_dir=$1
tile=$2


if [ "$tile" == "vm" ]; then
    for i in {1..5}; do
        gnuplot \
            -e "row1='$base_dir/vm$i-data/data/net/eth0/sbytes'"       -e "title1='VM $i - Bytes sent'"\
            -e "row2='$base_dir/vm$i-data/data/net/eth0/rbytes'"       -e "title2='VM $i - Bytes recv'" \
            -e "row3='$base_dir/vm$i-data/data/stat/cpu/user_time'"    -e "title3='VM $i - User time'" \
            -e "row4='$base_dir/vm$i-data/data/disks/xvda/writes'"     -e "title4='VM $i - Disk writes'" \
            -e "row5='$base_dir/vm$i-data/data/disks/xvda/reads'"      -e "title5='VM $i - Disk reads'" \
            multiplot-5 > vm-${i}.png
    done
fi

if [ "$tile" == "attr" ]; then
    for i in net/eth0/sbytes net/eth0/rbytes stat/cpu/user_time disks/xvda/total_time disks/xvda/reads disks/xvda/writes; do
        name=$(echo "$i" | tr '/' '-')
        gnuplot \
            -e "row1='$base_dir/vm1-data/data/$i'" -e "title1='VM1 $i'"\
            -e "row2='$base_dir/vm2-data/data/$i'" -e "title2='VM2 $i'" \
            -e "row3='$base_dir/vm3-data/data/$i'" -e "title3='VM3 $i'" \
            -e "row4='$base_dir/vm4-data/data/$i'" -e "title4='VM4 $i'" \
            -e "row5='$base_dir/vm5-data/data/$i'" -e "title5='VM5 $i'" \
            multiplot-5 > attr-${name}.png
    done
fi
