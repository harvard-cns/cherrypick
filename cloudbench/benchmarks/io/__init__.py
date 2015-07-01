""" Benchmark module for measuring disk-IO capacity of the machine.

This module has two benchmarks:
    * fio
    * bonnie

fio performs two tests on the machine:
    Random access: 70 read / 30 write, with block size of 8kB
    Random access: 100 read / 0 write, with block size of 4kB

The results are reported as:

    {
        server_location: Location (data-center) of the server
        r70: Random access 70% read throughput (8kB)
        r30: Random access 30% read throughput (8kB)
        r100: Random access read throughput (4kB)
    }

"""

from .main import fio

__all__ = ['fio']
