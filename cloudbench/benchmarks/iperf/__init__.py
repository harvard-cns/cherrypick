""" Benchmark module for measuring network throughput by using iperf
between two virtual machines.

iperf reports a result in the following format:

    {
        server_location: Location (data-center) of the server
        client_location: Location (data-center) of the client
        server_ip: IP of the server machine
        client_ip: IP of the client machine
        server_port: Port used by the server, typically, 5001
        client_port: Port used by the client.
        bandwidth: Bandwidth of the server in bits per second.
    }

"""

from .main import iperf, iperf_vnet

__all__ = ['iperf', 'iperf_vnet']
