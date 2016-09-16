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
    # ...

    # Spark Regression Parameters
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

    # If exp is TPCH
    if [ $exp = "tpch" ]; then
        params="$params,tpch:runs=$TPCH_RUNS"
        params="$params,tpch:scale=$TPCH_SCALE"
    fi

    # If exp is Spark
    if [ $exp = "spark" ]; then
        # Nothing to do for spark regression right now
        echo -n
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
    sleep 1

    # Execute
    echo "> Executing: $expSpec"
    printf "%s\0" $paramsQ $expQ $cloudQ $verboseQ | \
        xargs -0 bash -c './cb "$@"' --
    sleep 1

    exit 0

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
    # configFor "spark" "r3.large" "8" "ebs"
    # configFor "spark" "m4.large" "8" "ebs"

    # configFor "spark" "c4.xlarge" "4" "ebs"
    # configFor "spark" "r3.xlarge" "4" "ebs"
    # configFor "spark" "m4.xlarge" "4" "ebs"

    # configFor "spark" "c4.2xlarge" "2" "ebs"
    # configFor "spark" "r3.2xlarge" "2" "ebs"
    # configFor "spark" "m4.2xlarge" "2" "ebs"

    # configFor "spark" "c4.large" "16" "ebs"
    # configFor "spark" "c4.xlarge" "8" "ebs"
    # configFor "spark" "c4.2xlarge" "10" "ebs"

    # configFor "spark" "r3.large" "16" "ebs"
    # configFor "spark" "r3.xlarge" "8" "ebs"
    # configFor "spark" "r3.2xlarge" "10" "ebs"

    # configFor "spark" "m4.large" "16" "ebs"
    # configFor "spark" "m4.xlarge" "8" "ebs"
    # configFor "spark" "m4.2xlarge" "10" "ebs"

    # configFor "spark" "c4.xlarge" "12" "ebs"
    # configFor "spark" "r3.xlarge" "12" "ebs"
    # configFor "spark" "m4.xlarge" "12" "ebs"

    # configFor "spark" "c4.xlarge" "16" "ebs"
    # configFor "spark" "c4.2xlarge" "4" "ebs"
    # configFor "spark" "c4.2xlarge" "6" "ebs"

    # configFor "spark" "r3.xlarge" "16" "ebs"
    # configFor "spark" "r3.2xlarge" "4" "ebs"
    # configFor "spark" "r3.2xlarge" "6" "ebs"

    # configFor "spark" "m4.xlarge" "16" "ebs"
    # configFor "spark" "m4.2xlarge" "4" "ebs"
    # configFor "spark" "m4.2xlarge" "6" "ebs"

    # configFor "spark" "c4.2xlarge" "8" "ebs"
    # configFor "spark" "r3.2xlarge" "8" "ebs"
    # configFor "spark" "m4.2xlarge" "8" "ebs"

    # configFor "spark" "i2.xlarge" "4"  "local"
    # configFor "spark" "i2.xlarge" "8"  "local"
    # configFor "spark" "i2.xlarge" "12" "local"
    # configFor "spark" "i2.xlarge" "16" "local"

    # configFor "spark" "i2.2xlarge" "2" "local"
    # configFor "spark" "i2.2xlarge" "4" "local"
    # configFor "spark" "i2.2xlarge" "6" "local"
    # configFor "spark" "i2.2xlarge" "8" "local"
    # configFor "spark" "i2.2xlarge" "10" "local"

    # configFor "tpch" "m4.large" "16" "ebs"
    # configFor "tpch" "c4.xlarge" "16" "ebs"
    # configFor "tpch" "r3.2xlarge" "6" "ebs"
    # configFor "tpch" "r3.large" "16" "ebs"
    # configFor "tpch" "m4.large" "24" "ebs"
    # configFor "tpch" "c4.large" "32" "ebs"

    configFor "spark" "m4.large" "24" "ebs"
    configFor "spark" "m4.large" "32" "ebs"
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

    # configFor "tpch" "m4.large" "40" "ebs"
}

########################################
# PARALLELIZATION
########################################

printConfigs | xargs -0 -n 4 -P 1 bash -c 'configExec "$@"' --
