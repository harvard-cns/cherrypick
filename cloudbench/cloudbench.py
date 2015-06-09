from environment import Env
import argparse

#TODO: Clean up
def main():
    import sys

    parser = argparse.ArgumentParser(prog='Cloudbench')

    parser.add_argument('--setup', action='store_true',
        default=False, help='Prepares the benchmark environment')
    parser.add_argument('--teardown', action='store_true',
        default=False, help='Teardown the benchmark'
        ' environment')
    parser.add_argument('--benchmark',
        help='Name of the benchmark that will be executed')

    parser.add_argument('--list', action='store_true', default=False,
        help='List all the benchmarks')

    args = parser.parse_args()

    if args.list:
        import os
        for d in os.walk('../cloudbench/benchmarks').next()[1]:
            print d
        return

    mod = __import__('benchmarks.' + args.benchmark + '.main',
            fromlist=['benchmarks.' + args.benchmark])

    env = Env('azure', "../cloudbench/benchmarks/" +
            args.benchmark + "/config.xml")

    if args.setup:
        env.setup()

    mod.run(env)

    if args.teardown:
        env.teardown()
