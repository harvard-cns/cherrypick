#!/bin/bash

benchmarks=(m3 m3-standard m4 t2)
records=(100 30 3 1)
reducers=(10 20 40 80 160)

run_terasort() {
    bench=$1
    terasort_rows=$2
    terasort_reducers=$3

    # Run the experiment
    ./cb --benchmark=$bench --cloud=aws --params="terasort:rows=$terasort_rows,terasort:mappers=50,terasort:reducers=$terasort_reducers"
    sleep 10

    # Move the results to the exp folder
    mkdir exp-$bench-$terasort_rows-$terasort_reducers
    mv vm* exp-$bench-$terasort_rows-$terasort_reducers
    mv *.large exp-$bench-$terasort_rows-$terasort_reducers/time
    return 0;
}

for bench in ${benchmarks[@]}; do
    ./cb --benchmark=$bench --cloud=aws --setup --no-execute
    sleep 30

    for record in ${records[@]}; do
        num_records=$(bc <<< "$record*10000000")
        for reducer in ${reducers[@]}; do
            echo "Running $bench (reducers: $reducer, data: $record GB)"
            # Setup the experiment
            run_terasort $bench $num_records $reducer
            sleep 30
        done
    done

    # Make sure we teardown everything correctly
    ./cb --benchmark=$bench --cloud=aws --teardown --no-execute
    sleep 60
    ./cb --benchmark=$bench --cloud=aws --teardown --no-execute
    sleep 30
    ./cb --benchmark=$bench --cloud=aws --teardown --no-execute
done
