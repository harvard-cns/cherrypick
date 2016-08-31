#!/bin/bash


prefix=$1
instance_count=$2
benchmark_name="tpch-${2}-instances"
instance_type=$3
storage_type=$4
scale=$5
runs=$6

run_tpch() {
    tpch_scale=$1

    # Run the experiment
    ./cb --benchmark=$benchmark_name --cloud=aws --params="instance-type=$instance_type,tpch:scale=$tpch_scale,tpch:runs=$runs"
    sleep 10
    return 0;
}

./cb --benchmark=$benchmark_name --cloud=aws --setup --no-execute --params="storage=$storage_type,instance-type=$instance_type,placement-group=false" -vvvvv
sleep 30

echo "Running $instance_type (data: $scale GB)"
# Setup the experiment
run_tpch $scale
sleep 30

# Make sure we teardown everything correctly
./cb --benchmark=$benchmark_name --cloud=aws --teardown --no-execute --params="storage=$storage_type,instance-type=$instance_type,placement-group=false" -vvvvv
sleep 60
./cb --benchmark=$benchmark_name --cloud=aws --teardown --no-execute --params="storage=$storage_type,instance-type=$instance_type,placement-group=false" -vvvvv
sleep 30
./cb --benchmark=$benchmark_name --cloud=aws --teardown --no-execute --params="storage=$storage_type,instance-type=$instance_type,placement-group=false" -vvvvv
