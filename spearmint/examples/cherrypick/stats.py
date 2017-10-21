#!/bin/bash

percentile() {
    awk "{
            count[NR] = \$$1;
        }
        END {
            print count[int(((NR * $2) + 0.5)/100)];
        }"
}

avg() {
    awk "{sum+=\$$1; count+=1}END{print sum/count}"
}

std() {
    awk "{sqsum+=\$$1*\$$1; sum+=\$$1; count+=1}END{std=sqrt((sqsum/count)-(sum/count)*(sum/count)); print std}"
}

echo -e "Experiment\tEC\tET\tEB\tCC\tCT\tCB\tOptimality\tCCStd\tCTStd\tCBStd\tCpC\tCpT\tCpB\tCpSC\tCpST\tCpSB"
for exp in kmeans spark tpcds tpch terasort; do
    python cherrypick_best.py $exp > tmp.tsv
    exh_cost=$(cat tmp.tsv | awk '{sum += $4}END{print sum}')
    exh_time=$(cat tmp.tsv | awk '{sum += $5}END{print sum}')
    exh_best=$(cat tmp.tsv | tail -n 1 | awk '{print $4}')

    python coordinate-resource.py $exp | sort -nk5,5  > tmp.tsv
    cc=$(cat tmp.tsv  | sort -nk5,5  | percentile 5 50)
    cc_low=$(cat tmp.tsv  | sort -nk5,5  | percentile 5 10)
    cc_high=$(cat tmp.tsv  | sort -nk5,5  | percentile 5 90)

    ct=$(cat tmp.tsv | sort -nk6,6 | percentile 6 50)
    ct_low=$(cat tmp.tsv | sort -nk6,6 | percentile 6 10)
    ct_high=$(cat tmp.tsv | sort -nk6,6 | percentile 6 90)

    cb=$(cat tmp.tsv | sort -nk7,7 | percentile 7 50)
    cb_low=$(cat tmp.tsv | sort -nk7,7 | percentile 7 10)
    cb_high=$(cat tmp.tsv  | sort -nk7,7 | percentile 7 90)

    cat 'exp-with-kmeans.log' | grep $exp > tmp.tsv

    cpc=$(cat tmp.tsv | sort -nk 6,6 | percentile 6 50)
    cpc_low=$(cat tmp.tsv | sort -nk 6,6 | percentile 6 10)
    cpc_high=$(cat tmp.tsv | sort -nk 6,6 | percentile 6 90)

    cpt=$(cat tmp.tsv | sort -nk 5,5 | percentile 5 50)
    cpt_low=$(cat tmp.tsv | sort -nk 5,5 | percentile 5 10)
    cpt_high=$(cat tmp.tsv | sort -nk 5,5 | percentile 5 90)

    cpb=$(cat tmp.tsv | sort -nk 3,3 | percentile 3 50)
    cpb_low=$(cat tmp.tsv | sort -nk 3,3 | percentile 3 10)
    cpb_high=$(cat tmp.tsv | sort -nk 3,3 | percentile 3 90)

    ratio=$(echo "scale=4; $coo_best/$exh_best * 100.0" | bc -l)

    echo -e "$exp,$cpc,$cpc_low,$cpc_high,$cc,$cc_low,$cc_high,$ct,$ct_low,$ct_high,$cc,$cc_low,$cc_high,$cb,$cb_low,$cb_high,$cb,$cb_low,$cb_high,$cpb,$cpb_low,$cpb_high\n"
done
