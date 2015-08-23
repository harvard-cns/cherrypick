#!/bin/bash

benchmarks=(c4 m4 m3 t2)
benchmarks=(m3 t2)

for bench in ${benchmarks[@]}; do
    echo "Running $bench."
    # Setup the experiment
    ./cb --benchmark=$bench --cloud=aws --setup --no-execute
    sleep 30

    # Run the experiment
    ./cb --benchmark=$bench --cloud=aws
    sleep 10

    # Move the results to the exp folder
    mkdir exp-$bench
    mv vm* exp-$bench

    # Make sure we teardown everything correctly
    ./cb --benchmark=$bench --cloud=aws --teardown --no-execute
    sleep 60
    ./cb --benchmark=$bench --cloud=aws --teardown --no-execute
    sleep 30
    ./cb --benchmark=$bench --cloud=aws --teardown --no-execute
done
