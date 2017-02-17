#!/bin/bash

configExec() {
    exp="$1"
    iType="$2"
    iCount="$3"
    dType="$4"

    outputDir="$exp-$iType-$iCount-results"
    experiment="final-$exp-template"
    root=".."

    ########################################
    # Generate the benchmark
    ########################################
    local expName=$(./gen.sh -b $experiment -c $root -n $iCount)
    expName=$(echo $expName | xargs)

    if [ -z $expName ]; then
        echo "No such experiment ($experiment) was found."
        exit 1
    fi

    if [ $? -ne 0 ]; then 
        echo "Error: could not create experiment for $outputDir";
        exit 1
    fi


    ########################################
    # DEFAULT Parameters
    ########################################

    # TPCH Parameters
    TPCH_RUNS=2
    TPCH_SCALE=100

    # Terasort Parameters
    TERASORT_SCALE=330

    # Spark Regression Parameters
    SPARK_ML_EXAMPLES=250000

    # Spark KMeans Parameters
    # ...
    
    # TPCDS Parameters
    # ...

    ########################################
    # Initialize the parameter used by the cb script
    ########################################
    expSpec="$expName: ($exp, $iType, $iCount, $dType)"
    echo "Running $expSpec"

    # Build the benchmark parameters
    params="placement-group=false"
    params="$params,instance-type=$iType"
    if [ $dType = "ebs" ]; then
        params="$params,storage=gp2-2-250"
    fi

    # If exp is TPCDS
    if [ $exp = "tpch" ]; then
        echo -n
    fi

    # If exp is TPCH
    if [ $exp = "tpch" ]; then
        params="$params,tpch:runs=$TPCH_RUNS"
        params="$params,tpch:scale=$TPCH_SCALE"
    fi

    # If exp is Spark
    if [ $exp = "spark" ]; then
        # Nothing to do for spark regression right now
        params="$params,sparkml:examples=$SPARK_ML_EXAMPLES"
    fi

    # If exp is Kmeans
    if [ $exp = "kmeans" ]; then
        params="$params,kmeans:examples=$SPARK_ML_EXAMPLES"
    fi

    # If exp is Terasort
    if [ $exp = "terasort" ]; then
        scale=$(echo "$TERASORT_SCALE*10000000" | bc)
        params="$params,terasort:rows=$scale"
    fi

    paramsQ="--params=$params"
    expQ="--benchmark=$expName"
    cloudQ="--cloud=aws"
    noExecQ="--no-execute"
    setupQ="--setup"
    teardownQ="--teardown"
    verboseQ="-vvvv"

    cbBaseInput=$(printf "%s\0%s\0%s\0" $expQ $cloudQ $verboseQ)
    cbExecute=$(printf "%s\0" $cbBaseInput $paramsQ)

    cbNoExecute=$(printf "%s\0" $cbBaseInput $noExecQ)
    cbSetup=$(printf "%s\0" $cbNoExecute $setupQ)
    cbTeardown=$(printf "%s\0" $cbNoExecute $teardownQ)

    ########################################
    # Run the experiment
    ########################################

    # Setup
    echo "> Setting up: $expSpec"
    printf "%s\0" $setupQ $noExecQ $paramsQ $expQ $cloudQ $verboseQ | \
        xargs -0 bash -c './cb "$@"' --
    sleep 10

    # Execute
    echo "> Executing: $expSpec"
    printf "%s\0" $paramsQ $expQ $cloudQ $verboseQ | \
        xargs -0 bash -c './cb "$@"' --
    sleep 10

    out="Exit Done"

    # Teardown
    echo "> Tearing down: $expSpec"
    while [[ ! -z $out ]]; do
        out=$(
    printf "%s\0" $teardownQ $noExecQ $paramsQ $expQ $cloudQ $verboseQ | \
        xargs -0 bash -c './cb "$@"' --
        )
        sleep 10
    done

    echo "Teardown is complete: $expName"
}

export -f configExec

configFor() {
    exp="$1"
    iType="$2"
    iCount="$3"
    dType="$4"

    printf "%s\0%s\0%s\0%s\0" $exp $iType $iCount $dType
}

printConfigs() {
    echo -n
    configFor "kmeans" "m4.xlarge" "4" "ebs"
    # configFor "spark" "c4.large" "24" "ebs"
    # configFor "tpcds" "i2.xlarge" "32" ""
}

usage() {
    echo -n "run.sh [PARALLELIZATION LEVEL]

Please add the configs that you want to run to the printConfigs
function inside the script.  The syntax is:

> configFor \"Experiment\" \"InstanceType\" \"Machine Count\" \"Disk Type\"

1) Experiment: any one of: tpcds, tpch, tera, spark, kmeans
2) Instance type: any of the instance types in Amazon
3) Instance count: number of instances in the cluster
4) Disk type: ebs or empty string

By default the disks are set to be 2x250GB of gp2 type per instance.  
Feel free to change that within this file.
"
}

parallelization=${1:-no-value}

########################################
# PARALLELIZATION
########################################

if [[ "$parallelization" == "no-value" ]]; then
    usage
else
    printConfigs | xargs -0 -n 4 -P $parallelization bash -c 'configExec "$@"' --
fi

