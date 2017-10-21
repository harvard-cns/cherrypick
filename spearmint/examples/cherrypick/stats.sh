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

LOG=$1

HIGH=90
MED=50
LOW=10

for exp in kmeans spark tpcds tpch terasort; do
    python cherrypick_best.py $exp > tmp.tsv
    exh_cost=$(cat tmp.tsv | awk '{sum += $4}END{print sum}')
    exh_time=$(cat tmp.tsv | awk '{sum += $5}END{print sum}')
    exh_best=$(cat tmp.tsv | tail -n 1 | awk '{print $4}')

    python coordinate-resource.py $exp | sort -nk5,5  > tmp.tsv

    cc=$(cat tmp.tsv  | sort -nk5,5  | percentile 5 $MED)
    cc_low=$(cat tmp.tsv  | sort -nk5,5  | percentile 5 $LOW)
    cc_high=$(cat tmp.tsv  | sort -nk5,5  | percentile 5 $HIGH)
    cc=$(echo "scale=6; ($cc/$exh_cost)*100" | bc -l)
    cc_low=$(echo "scale=6; ($cc_low/$exh_cost)*100" | bc -l)
    cc_high=$(echo "scale=6; ($cc_high/$exh_cost)*100" | bc -l)

    ct=$(cat tmp.tsv | sort -nk6,6 | percentile 6 $MED)
    ct_low=$(cat tmp.tsv | sort -nk6,6 | percentile 6 $LOW)
    ct_high=$(cat tmp.tsv | sort -nk6,6 | percentile 6 $HIGH)
    ct=$(echo "scale=6; ($ct/$exh_time)*100" | bc -l)
    ct_low=$(echo "scale=6; ($ct_low/$exh_time)*100" | bc -l)
    ct_high=$(echo "scale=6; ($ct_high/$exh_time)*100" | bc -l)

    cb=$(cat tmp.tsv | sort -nk7,7 | percentile 7 $MED)
    cb_low=$(cat tmp.tsv | sort -nk7,7 | percentile 7 $LOW)
    cb_high=$(cat tmp.tsv  | sort -nk7,7 | percentile 7 $HIGH)
    cb=$(echo "scale=6; ($cb/$exh_best-1)*100" | bc -l)
    cb_low=$(echo "scale=6; ($cb_low/$exh_best-1)*100" | bc -l)
    cb_high=$(echo "scale=6; ($cb_high/$exh_best-1)*100" | bc -l)

    cat "$LOG" | grep $exp > tmp.tsv
    cpc=$(cat tmp.tsv | sort -nk 6,6 | percentile 6 $MED)
    cpc_low=$(cat tmp.tsv | sort -nk 6,6 | percentile 6 $LOW)
    cpc_high=$(cat tmp.tsv | sort -nk 6,6 | percentile 6 $HIGH)
    cpc=$(echo "scale=6; ($cpc/$exh_cost)*100" | bc -l)
    cpc_low=$(echo "scale=6; ($cpc_low/$exh_cost)*100" | bc -l)
    cpc_high=$(echo "scale=6; ($cpc_high/$exh_cost)*100" | bc -l)

    cpt=$(cat tmp.tsv | sort -nk 5,5 | percentile 5 $MED)
    cpt_low=$(cat tmp.tsv | sort -nk 5,5 | percentile 5 $LOW)
    cpt_high=$(cat tmp.tsv | sort -nk 5,5 | percentile 5 $HIGH)
    cpt=$(echo "scale=6; ($cpt/$exh_time)*100" | bc -l)
    cpt_low=$(echo "scale=6; ($cpt_low/$exh_time)*100" | bc -l)
    cpt_high=$(echo "scale=6; ($cpt_high/$exh_time)*100" | bc -l)

    cpb=$(cat tmp.tsv | sort -nk 3,3 | percentile 3 $MED)
    cpb_low=$(cat tmp.tsv | sort -nk 3,3 | percentile 3 $LOW)
    cpb_high=$(cat tmp.tsv | sort -nk 3,3 | percentile 3 $HIGH)

    echo -e "$exp	$cpc	$cpc_low	$cpc_high	$cc	$cc_low	$cc_high	$cpt	$cpt_low	$cpt_high	$ct	$ct_low	$ct_high	$cpb	$cpb_low	$cpb_high	$cb	$cb_low	$cb_high"
done
