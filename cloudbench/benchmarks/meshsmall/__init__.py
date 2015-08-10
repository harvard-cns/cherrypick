""" Module for performing full-mesh test across all the virtual machines
in different data-centers of the cloud provider.  There are three
categories of experiments:

    1) inter data-center pairwise virtual machine tests
        -- iperf, hping3
    2) intra data-center pairwise virtual machine tests
        -- iperf
    3) single virtual machine tests
        -- fio

The results are saved in the storage (env.storage()), which defaults to
Azure tables.

"""

