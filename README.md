# Cloudbench

Spearmint benchmarks are in the spearmint folder.  I'll write a guide on how to
run the spearmint experiments later.  We also made a few modifications to
Spearmint to speed up execution.

If you want to run your benchmarks using Cloudbench, you need to follow the
outdated guide below.  The last we checked (Feb 2017) the benchmarking platform
was compatible with AWS EC2.

# OUTDATED

    # Cloudbench

    This is a project which tries to benchmark and compare multiple public
    cloud providers. It also tries to identify the bottleneck resources in
    the cloud platform for applications.


    # Setup
    Put your keys in the ./config/ folder.  For Azure you would need to
    create two keys:

    * cloud.pem
    * cloud.key

    # Running the experiment

    Go to the script folder and use the run.sh script.  The default help is pretty
    self explanatory:

    >   Please add the configs that you want to run to the printConfigs
    >   function inside the script.  The syntax is:
    >
    >   > configFor "Experiment" "InstanceType" "Machine Count" "Disk Type"
    >
    >   1) Experiment: any one of: tpcds, tpch, tera, spark
    >
    >   2) Instance type: any of the instance types in Amazon
    >
    >   3) Instance count: number of instances in the cluster
    >
    >   4) Disk type: ebs or empty string
    >
    >   By default the disks are set to be 2x250GB of gp2 type per instance.  
    >   Feel free to change that within this file.

    <!--
    cloud.key should be a 2048bit RSA key.  You can generate Azure keys with
    the openssl command or just the supplied makefile:

    > make azure_keys

    Also make sure that the permission of *cloud.key* is set to 600.

    # Cloud specific notes

    ## Azure
    * Because of plethora of random objects that Azure creates for you, as of
    now, it is not possible to "cleanly" delete a topology.  This is a work
    in progress and any feedbacks are welcome


    ## Examples

    To run a specific benchmark you can use the 'bin/cb' binary.  For
    example:

    > ./cb --benchmark=ipref --setup --teardown


    This command would first setup the environment specified in config.xml
    for running the iperf benchmark located in cloudbench/benchmarks/iperf.
    Then it would run the main.py script for benchmarking, and afterwards it
    would teardown the environment.  If the environment is to be persisted
    for next runs, you can avoid passing --teardown to cb.

    ## Benchmark format

    All the benchmarks are located in the cloudbench/benchmarks/ folder.
    To create a new benchmark, e.g., stress_test , you would need to create
    a new folder called stress_test in the benchmarks folder.  At least two
    files are required:

    * *config.xml* which specifies the environment configuration, e.g.,
      virtual machines, virtual networks, etc.
    * *main.py* where the benchmarking script is run in the context of the
      environment.

    For an example, have a look at cloudbench/benchmarks/iperf.
    -->
