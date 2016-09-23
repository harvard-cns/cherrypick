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
        echo "Variable length is zero ..."
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
    # configFor "spark" "c4.large" "8" "ebs"
    configFor "spark" "r3.large" "8" "ebs"
    configFor "spark" "m4.large" "8" "ebs"

    configFor "spark" "c4.xlarge" "4" "ebs"
    configFor "spark" "r3.xlarge" "4" "ebs"
    configFor "spark" "m4.xlarge" "4" "ebs"

    configFor "spark" "c4.2xlarge" "2" "ebs"
    configFor "spark" "r3.2xlarge" "2" "ebs"
    configFor "spark" "m4.2xlarge" "2" "ebs"

    configFor "spark" "c4.large" "16" "ebs"
    configFor "spark" "c4.xlarge" "8" "ebs"
    configFor "spark" "c4.2xlarge" "10" "ebs"

    configFor "spark" "r3.large" "16" "ebs"
    configFor "spark" "r3.xlarge" "8" "ebs"
    configFor "spark" "r3.2xlarge" "10" "ebs"

    configFor "spark" "m4.large" "16" "ebs"
    configFor "spark" "m4.xlarge" "8" "ebs"
    configFor "spark" "m4.2xlarge" "10" "ebs"

    configFor "spark" "c4.xlarge" "12" "ebs"
    configFor "spark" "r3.xlarge" "12" "ebs"
    configFor "spark" "m4.xlarge" "12" "ebs"

    configFor "spark" "c4.xlarge" "16" "ebs"
    configFor "spark" "c4.2xlarge" "4" "ebs"
    configFor "spark" "c4.2xlarge" "6" "ebs"

    configFor "spark" "r3.xlarge" "16" "ebs"
    configFor "spark" "r3.2xlarge" "4" "ebs"
    configFor "spark" "r3.2xlarge" "6" "ebs"

    configFor "spark" "m4.xlarge" "16" "ebs"
    configFor "spark" "m4.2xlarge" "4" "ebs"
    configFor "spark" "m4.2xlarge" "6" "ebs"

    configFor "spark" "c4.2xlarge" "8" "ebs"
    configFor "spark" "r3.2xlarge" "8" "ebs"
    configFor "spark" "m4.2xlarge" "8" "ebs"

    configFor "spark" "i2.xlarge" "12" "local"
    configFor "spark" "i2.xlarge" "8"  "local"
    configFor "spark" "i2.xlarge" "4"  "local"
    configFor "spark" "i2.xlarge" "16" "local"

    configFor "spark" "i2.2xlarge" "8" "local"
    configFor "spark" "i2.2xlarge" "4" "local"
    configFor "spark" "i2.2xlarge" "6" "local"
    configFor "spark" "i2.2xlarge" "2" "local"
    configFor "spark" "i2.2xlarge" "10" "local"

    # configFor "tpch" "m4.large" "16" "ebs"
    # configFor "tpch" "c4.xlarge" "16" "ebs"
    # configFor "tpch" "r3.2xlarge" "6" "ebs"
    # configFor "tpch" "r3.large" "16" "ebs"
    # configFor "tpch" "m4.large" "24" "ebs"
    # configFor "tpch" "c4.large" "32" "ebs"

    # configFor "spark" "m4.large" "24" "ebs"
    # configFor "spark" "m4.large" "32" "ebs"
    # configFor "spark" "m4.large" "40" "ebs"

    # configFor "spark" "m4.xlarge" "20" "ebs"

    # configFor "spark" "r3.xlarge" "20" "ebs"
    # configFor "spark" "r3.xlarge" "4" "ebs"

    # configFor "spark" "r3.large" "24" "ebs"
    # configFor "spark" "r3.large" "32" "ebs"
    # configFor "spark" "r3.large" "40" "ebs"

    # configFor "spark" "i2.xlarge" "20" "ebs"

    # configFor "spark" "c4.xlarge" "20" "ebs"

    # configFor "spark" "c4.large" "24" "ebs"
    # configFor "spark" "c4.large" "32" "ebs"
    # configFor "spark" "c4.large" "40" "ebs"
}

printSeqConfigs(){
    # configFor "spark" "m4.large" "24" "ebs"
    # configFor "spark" "m4.large" "32" "ebs"
    configFor "spark" "m4.large" "40" "ebs"

    configFor "spark" "m4.xlarge" "20" "ebs"

    configFor "spark" "r3.xlarge" "20" "ebs"
    configFor "spark" "r3.xlarge" "4" "ebs"

    configFor "spark" "r3.large" "24" "ebs"
    configFor "spark" "r3.large" "32" "ebs"
    configFor "spark" "r3.large" "40" "ebs"

    configFor "spark" "i2.xlarge" "20" "ebs"

    configFor "spark" "c4.xlarge" "20" "ebs"

    configFor "spark" "c4.large" "24" "ebs"
    configFor "spark" "c4.large" "32" "ebs"
    configFor "spark" "c4.large" "40" "ebs"
}

printFailedConfigs() {
    #configFor "spark" "r3.xlarge" "12" "ebs"
    #configFor "spark" "r3.xlarge" "16" "ebs"
    #configFor "spark" "r3.xlarge" "8" "ebs"
    #configFor "spark" "c4.large" "32" "ebs"
    # configFor "spark" "c4.xlarge" "12" "ebs"
    # configFor "spark" "c4.2xlarge" "10" "ebs"
    # configFor "spark" "i2.xlarge" "8" "ebs"
    # configFor "spark" "i2.xlarge" "12" "ebs"
    # configFor "spark" "m4.2xlarge" "8" "ebs"
    configFor "spark" "r3.large" "24" "ebs"
}

printFailedSeqConfigs() {
    #configFor "spark" "c4.large" "48" "ebs"
    #configFor "spark" "c4.large" "56" "ebs"
    #configFor "spark" "c4.xlarge" "24" "ebs"
    #configFor "spark" "c4.xlarge" "28" "ebs"
    #configFor "spark" "c4.2xlarge" "12" "ebs"
    #configFor "spark" "c4.2xlarge" "14" "ebs"

    #configFor "spark" "m4.large" "48" "ebs"
    #configFor "spark" "m4.large" "56" "ebs"
    #configFor "spark" "m4.xlarge" "24" "ebs"
    #configFor "spark" "m4.xlarge" "28" "ebs"
    #configFor "spark" "m4.2xlarge" "12" "ebs"
    #configFor "spark" "m4.2xlarge" "14" "ebs"

    #configFor "spark" "r3.large" "48" "ebs"
    #configFor "spark" "r3.large" "56" "ebs"
    #configFor "spark" "r3.xlarge" "24" "ebs"
    #configFor "spark" "r3.xlarge" "28" "ebs"
    #configFor "spark" "r3.2xlarge" "12" "ebs"
    #configFor "spark" "r3.2xlarge" "14" "ebs"

    #configFor "spark" "i2.xlarge" "24" "ebs"
    #configFor "spark" "i2.xlarge" "28" "ebs"
    #configFor "spark" "i2.2xlarge" "12" "ebs"
    #configFor "spark" "i2.2xlarge" "14" "ebs"

    #configFor "spark" "r3.xlarge" "12" "ebs"
    configFor "spark" "r3.xlarge" "8" "ebs"
    configFor "spark" "r3.2xlarge" "4" "ebs"
    configFor "spark" "m4.2xlarge" "10" "ebs"
}

usage() {
    echo -n "run.sh [PARALLELIZATION LEVEL]

Please add the configs that you want to run to the printConfigs
function inside the script.  The syntax is:

> configFor \"Experiment\" \"InstanceType\" \"Machine Count\" \"Disk Type\"

1) Experiment: any one of: tpcds, tpch, tera, spark
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
    echo -n
    #printConfigs | xargs -0 -n 4 -P 1 bash -c 'configExec "$@"' --
fi
