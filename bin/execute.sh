#!/bin/bash

benchmarks=(m3 m3-standard m4 t2)
records=(100 30 10 3 1)
reducers=(10 20 40 80 160)

storages=(standard gp2)
benchmarks=(m3.large m4.large m3.xlarge m4.xlarge m3.medium c4.xlarge c4.large c4.2xlarge r3.large r3.xlarge t2.large)

storages=(standard gp2)
benchmarks=(m3.large m4.large m3.xlarge m4.xlarge m3.medium c4.xlarge c4.large c4.2xlarge r3.xlarge t2.large)

records=(1 10 30)
reducers=(10)

prefix=exp4

run_terasort() {
    bench=$1
    storage=$2
    terasort_rows=$3
    terasort_reducers=$4

    # Run the experiment
    ./cb --benchmark=generic-terasort --cloud=aws --params="terasort:rows=$terasort_rows,terasort:mappers=50,terasort:reducers=$terasort_reducers,instance-type=$bench,storage-type=$storage,placement-group=false"
    sleep 10

    # Move the results to the exp folder
    mkdir $prefix-$bench-$storage-$terasort_rows-$terasort_reducers
    mv vm* $prefix-$bench-$storage-$terasort_rows-$terasort_reducers
    mv *.out $prefix-$bench-$storage-$terasort_rows-$terasort_reducers/mapreduce_output
    mv *.time $prefix-$bench-$storage-$terasort_rows-$terasort_reducers/time
    return 0;
}

for storage in ${storages[@]}; do
    for bench in ${benchmarks[@]}; do
        ./cb --benchmark=generic-terasort --cloud=aws --setup --no-execute --params="instance-type=$bench,storage-type=$storage,placement-group=false" -vvvvv
        sleep 30

        for record in ${records[@]}; do
            num_records=$(bc <<< "$record*10000000")
            for reducer in ${reducers[@]}; do
                echo "Running $bench (reducers: $reducer, data: $record GB)"
                # Setup the experiment
                run_terasort $bench $storage $num_records $reducer
                sleep 30
            done
        done

        # Make sure we teardown everything correctly
        ./cb --benchmark=generic-terasort --cloud=aws --teardown --no-execute --params="instance-type=$bench,storage-type=$storage,placement-group=false" -vvvvv
        sleep 60
        ./cb --benchmark=generic-terasort --cloud=aws --teardown --no-execute --params="instance-type=$bench,storage-type=$storage,placement-group=false" -vvvvv
        sleep 30
        ./cb --benchmark=generic-terasort --cloud=aws --teardown --no-execute --params="instance-type=$bench,storage-type=$storage,placement-group=false" -vvvvv
    done
done
