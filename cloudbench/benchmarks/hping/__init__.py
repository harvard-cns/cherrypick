""" Benchmark module for measuring latency between two virtual machines
by using hping3.  As some of the cloud providers (e.g., Azure) have
blocked ICMP messages, it is not possible to use these to perform pings.
Of course, hping output differs from ping, as it also includes the
overhead of network stack of the other machine


The hping test performs a series of 20 pings to the server, and reports
the following results:

    {
        server_location: Location (data-center) of the server
        client_location: Location (data-center) of the client
        rtt_avg : Average latency of the 20 pings
        rtt_0   : Minimum latency of the pings
        rtt_10  : 10 percentile of the pings, i.e., the second lowest ping
        rtt_50  : Median of the pings
        rtt_90  : 90 percentile of the pings, i.e., the second largest ping
        rtt_100 : Maximum latency of the pings
    }

"""

from .main import hping

__all__ = ['hping']
